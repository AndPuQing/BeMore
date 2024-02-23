FROM python:3.12-alpine

WORKDIR /app/

# Define build argument for mirror usage
ARG USE_MIRROR=false

# Install Poetry
RUN if [ "$USE_MIRROR" = "true" ] ; then pip install poetry --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple ; else pip install poetry --no-cache-dir ; fi && poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN if [ "$USE_MIRROR" = "true" ] ; then poetry self add https://pypi.tuna.tsinghua.edu.cn/packages/a8/ea/1a6df188d97a2f762a92e6df8ce75e0d25e6caefaa3a079c2d4efae7d721/poetry_plugin_pypi_mirror-0.4.1-py3-none-any.whl#sha256=51d1fabd782e670bfeb66beaf821df462649d8f6147c7efb02d1c71fe3c17f7b ; fi
RUN if [ "$USE_MIRROR" = "true" ] ; then sh -c "if [ $INSTALL_DEV == 'true' ] ; then POETRY_PYPI_MIRROR_URL=https://pypi.tuna.tsinghua.edu.cn/simple poetry install --no-root ; else POETRY_PYPI_MIRROR_URL=https://pypi.tuna.tsinghua.edu.cn/simple poetry install --no-root --only main ; fi" ; else sh -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi" ; fi

ENV C_FORCE_ROOT=1

COPY ./app /app
WORKDIR /app

ENV PYTHONPATH=/app

COPY ./app/worker-start.sh /worker-start.sh

RUN chmod +x /worker-start.sh

CMD ["sh", "/worker-start.sh"]
