import collections
import inspect
import os
import random
from datetime import datetime, timedelta
from typing import Union

import gensim
from celery import Task
from celery.utils.log import get_task_logger
from gensim.models.doc2vec import TaggedDocument
from implicit.als import AlternatingLeastSquares
from pandas import DataFrame, Series
from rectools import Columns
from rectools.dataset import Dataset
from rectools.metrics import MAP, MeanInvUserFreq, Serendipity, calc_metrics
from rectools.models import ImplicitALSWrapperModel
from sklearn.model_selection import train_test_split
from sqlmodel import Session, select

from app import source
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models import CrawledItem, FeedBack, Item
from app.source.base import PaperRequestsTask

os.environ["OPENBLAS_NUM_THREADS"] = "1"  # For implicit ALS
logger = get_task_logger(__name__)


@celery_app.on_after_configure.connect  # type: ignore
def setup_periodic_tasks(sender, **kwargs):
    # sender.add_periodic_task(
    #     crontab(minute="10"),
    #     paper_crawler.s(),
    #     name="crawl papers",
    # )
    pass


members = inspect.getmembers(source, inspect.isclass)
for name, _class in members:
    # auto register task
    celery_app.register_task(_class)


def batch(iterable: Union[set[str], list[str]], n: int = 1):
    """
    Batch generator.

    :param iterable: iterable object.
    :param n: batch size.
    """
    iterable = list(iterable)
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]


class DatabaseTask(Task):
    @property
    def db(self) -> Session:
        """
        Lazy loading of database connection.
        """
        from app.db.engine import engine

        return Session(engine)


@celery_app.task(
    acks_late=True,
    base=DatabaseTask,
    bind=True,
    ignore_result=True,
)
def paper_crawler(self: DatabaseTask) -> None:
    """
    Celery task to crawl papers from arxiv.
    """
    for name, _class in members:
        if issubclass(_class, PaperRequestsTask):
            urls = _class.get_urls()
            # duplicate urls
            urls = list(set(urls))
            # duplicate usls from db
            with self.db as db:  # noqa: WPS440
                crawled_urls = db.exec(
                    select(CrawledItem).where(
                        (CrawledItem.last_crawled - datetime.now())
                        <= timedelta(days=7)
                    )
                )
                crawled_urls = [item.raw_url for item in crawled_urls]
            urls = list(set(urls) - set(crawled_urls))
            if len(urls) > settings.REQUESTS_BATCH_SIZE:
                for batch_urls in batch(urls, settings.REQUESTS_BATCH_SIZE):
                    logger.info(
                        f"Start crawling {name} with {len(batch_urls)} urls"
                    )
                    celery_app.send_task(name, args=[batch_urls])
            else:
                logger.info(f"Start crawling {name} with {len(urls)} urls")
                celery_app.send_task(name, args=[urls])
        else:
            logger.info(f"Start crawling {name}")
            celery_app.send_task(name)


@celery_app.task(
    acks_late=True,
    base=DatabaseTask,
    bind=True,
    ignore_result=True,
)
def train_doc2vec(self: DatabaseTask) -> None:
    # Step 1: Data Preprocessing
    with self.db as db:
        papers = db.exec(
            select(Item)
        )  # TODO: Do we need to limit the number of papers?
        documents = [paper.abstract for paper in papers]

    documents = random.sample(documents, settings.DATA_SIZE)

    def preprocess(docs, tokens_only=False):
        for i, doc in enumerate(docs):
            # remove punctuation
            doc = gensim.parsing.preprocessing.strip_punctuation(doc)
            # tokenize
            tokens = gensim.utils.simple_preprocess(doc)
            if tokens_only:
                yield tokens
            else:
                # For training data, add tags
                yield gensim.models.doc2vec.TaggedDocument(tokens, [i])

    train_corpus: list[TaggedDocument] = list(preprocess(documents))  # type: ignore

    # Step 2: Train the model
    model = gensim.models.doc2vec.Doc2Vec(
        vector_size=50, min_count=2, epochs=40
    )
    model.build_vocab(train_corpus)
    model.train(
        train_corpus, total_examples=model.corpus_count, epochs=model.epochs
    )

    # Step 3: Evaluate the model
    ranks = []
    second_ranks = []
    for doc_id in range(len(train_corpus)):
        inferred_vector = model.infer_vector(train_corpus[doc_id].words)
        sims = model.dv.most_similar([inferred_vector], topn=len(model.dv))
        rank = [docid for docid, sim in sims].index(doc_id)
        ranks.append(rank)

        second_ranks.append(sims[1])

    counter = collections.Counter(ranks)
    logger.info(f"Counter: {counter}")

    # Inferring
    with self.db as db:
        papers = db.exec(select(Item))
        for paper in papers:
            abstract = paper.abstract
            abstract = gensim.parsing.preprocessing.strip_punctuation(abstract)
            tokens = gensim.utils.simple_preprocess(abstract)
            inferred_vector = model.infer_vector(tokens)
            paper.doc2vec = inferred_vector
            db.add(paper)
        db.commit()
    logger.info("Inferred vectors saved")


def byte_to_list_float(byte: bytes):
    import struct

    return list(struct.unpack("f" * (len(byte) // 4), byte))


@celery_app.task(
    acks_late=True,
    base=DatabaseTask,
    bind=True,
    ignore_result=True,
)
def train_recommender_and_inference(self: DatabaseTask) -> None:

    # Step 1: Data Preprocessing
    with self.db as db:
        feedbacks = db.exec(select(FeedBack))
        feedbacks = [
            (
                feedback.user_id,
                feedback.item_id,
                feedback.feedback_type,
                feedback.timestamp,
            )
            for feedback in feedbacks
        ]
        interactions_df = DataFrame(
            feedbacks,
            columns=[
                Columns.User,
                Columns.Item,
                Columns.Weight,
                Columns.Datetime,
            ],
        )
        # datetime to timestamp
        interactions_df[Columns.Datetime] = interactions_df[
            Columns.Datetime
        ].map(lambda x: int(x.timestamp()))

    with self.db as db:
        papers = db.exec(select(Item))
        documents = [(paper.id, paper.doc2vec) for paper in papers]
        item_features_df = DataFrame(
            documents, columns=[Columns.Item, "doc2vec"]
        )
        # Select only items that present in the feedbacks table
        item_features_df = item_features_df[
            item_features_df[Columns.Item].isin(
                interactions_df[Columns.Item].unique()
            )
        ]
        item_features_df["doc2vec"] = item_features_df["doc2vec"].map(
            byte_to_list_float
        )
        # unpack doc2vec
        #        id  doc2vec
        # 0  1  [0.1, 0.2, 0.3, 0.4, 0.5]
        # to
        #        id  doc2vec_0  doc2vec_1  doc2vec_2  doc2vec_3  doc2vec_4
        # 0  1         0.1         0.2         0.3         0.4         0.5
        item_features_df = item_features_df.join(
            other=DataFrame(
                item_features_df['doc2vec'].apply(Series).add_prefix('doc2vec_')
            )
        ).drop(columns=["doc2vec"])

    # TODO(PuQing): drop the cold feedbacks
    train, test = train_test_split(
        interactions_df, test_size=0.2, random_state=32
    )
    test_users = test[Columns.User].unique()
    catalog = train[Columns.Item].unique()

    item_features_df = item_features_df[
        item_features_df[Columns.Item].isin(catalog)
    ]

    dataset_no_features = Dataset.construct(
        interactions_df=interactions_df,
    )

    dataset_full_features = Dataset.construct(
        interactions_df=train,
        # user_features_df=user_features,
        # cat_user_features=["sex", "age", "income"],
        item_features_df=item_features_df,
        make_dense_item_features=True,
    )

    dataset_item_features = Dataset.construct(
        interactions_df=train,
        item_features_df=item_features_df,
        make_dense_item_features=True,
    )

    dataset_user_features = Dataset.construct(
        interactions_df=train,
    )

    feature_datasets = {
        "full_features": dataset_full_features,
        "item_features": dataset_item_features,
        "user_features": dataset_user_features,
    }

    # Prepare dataset with biases as features

    item_biases = DataFrame({"id": catalog, "bias": 1})
    user_biases = DataFrame({"id": train[Columns.User].unique(), "bias": 1})

    dataset_with_biases = Dataset.construct(
        interactions_df=train,
        user_features_df=user_biases,
        make_dense_user_features=True,
        item_features_df=item_biases,
        make_dense_item_features=True,
    )
    feature_datasets["biases"] = dataset_with_biases

    metrics_name = {
        'MAP': MAP,
        'MIUF': MeanInvUserFreq,
        'Serendipity': Serendipity,
    }
    metrics = {}
    for metric_name, metric in metrics_name.items():
        for k in (1, 5, 10):
            metrics[f'{metric_name}@{k}'] = metric(k=k)

    K_RECOS = 10
    NUM_THREADS = 32
    RANDOM_STATE = 32
    ITERATIONS = 10

    def make_base_model(
        factors: int,
        regularization: float,
        alpha: float,
        fit_features_together: bool = False,
    ):
        return ImplicitALSWrapperModel(
            AlternatingLeastSquares(
                factors=factors,
                regularization=regularization,
                alpha=alpha,
                random_state=RANDOM_STATE,
                use_gpu=False,
                num_threads=NUM_THREADS,
                iterations=ITERATIONS,
            ),
            fit_features_together=fit_features_together,
        )

    alphas = [1, 10, 100]
    regularizations = [0.01, 0.1, 0.5]
    factors = [32, 64, 128]
    results = []
    dataset = dataset_no_features

    for alpha in alphas:
        for regularization in regularizations:
            for n_factors in factors:
                model_name = f"no_features_factors_{n_factors}_alpha_{alpha}_reg_{regularization}"
                model = make_base_model(
                    factors=n_factors,
                    regularization=regularization,
                    alpha=alpha,
                )
                model.fit(dataset)
                recos = model.recommend(
                    users=test_users,
                    dataset=dataset,
                    k=K_RECOS,
                    filter_viewed=True,
                )

                metric_values = calc_metrics(
                    metrics, recos, test, train, catalog
                )
                metric_values["model"] = model_name  # type: ignore
                results.append(metric_values)

    pure_df = (
        DataFrame(results)
        .set_index("model")
        .sort_values(by=["MAP@10", "Serendipity@10"], ascending=False)
    )

    # Best params for MAP@10
    best_params = pure_df.index[0]

    # Best grid search params for pure iALS models
    factors_options = (32, 64, 128)
    ALPHA = float(best_params.split("_")[5])
    REG = float(best_params.split("_")[7])

    # We have two options for training iALS with features in RecTools
    fit_features_together = (True, False)

    # We have datasets with different feature selections
    feature_datasets.keys()
    features_results = []
    for dataset_name, dataset in feature_datasets.items():
        for n_factors in factors_options:
            for features_option in fit_features_together:
                model_name = f"{dataset_name}_factors_{n_factors}_fit_together_{features_option}"
                model = make_base_model(
                    factors=n_factors,
                    regularization=REG,
                    alpha=ALPHA,
                    fit_features_together=features_option,
                )
                model.fit(dataset)
                recos = model.recommend(
                    users=test_users,
                    dataset=dataset,
                    k=K_RECOS,
                    filter_viewed=True,
                )
                metric_values = calc_metrics(
                    metrics, recos, test, train, catalog
                )
                metric_values["model"] = model_name  # type: ignore
                features_results.append(metric_values)

    features_df = (
        DataFrame(features_results)
        .set_index("model")
        .sort_values(by=["MAP@10", "Serendipity@10"], ascending=False)
    )
    print(features_df['MAP@10'])
