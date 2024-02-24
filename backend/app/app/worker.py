import collections
import inspect
import random
from datetime import datetime, timedelta
from typing import Union

import gensim
from celery import Task
from celery.utils.log import get_task_logger
from gensim.models.doc2vec import TaggedDocument
from sqlmodel import Session, select

from app import source
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models import CrawledItem, Item
from app.source.base import PaperRequestsTask

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
            with self.db as db:
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

    DATA_SIZE = 100
    documents = random.sample(documents, DATA_SIZE)

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


@celery_app.task(
    acks_late=True,
    base=DatabaseTask,
    bind=True,
    ignore_result=True,
)
def train_recommender(self: DatabaseTask) -> None:
    # Step 1: Data Preprocessing
    with self.db as db:
        papers = db.exec(select(Item))
