FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

WORKDIR /app/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "poetry self add poetry-plugin-pypi-mirror"
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then POETRY_PYPI_MIRROR_URL=https://pypi.tuna.tsinghua.edu.cn/simple poetry install --no-root ; else POETRY_PYPI_MIRROR_URL=https://pypi.tuna.tsinghua.edu.cn/simple poetry install --no-root --only main ; fi"


COPY ./app /app
ENV PYTHONPATH=/app
