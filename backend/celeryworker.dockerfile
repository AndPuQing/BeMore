FROM python:3.13

WORKDIR /app/

# Install Poetry
RUN pip install poetry --no-cache-dir && poetry config virtualenvs.create false


# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN sh -c "if [ '$INSTALL_DEV' == 'true' ] ; then poetry install --no-root ; else poetry install --no-root ; fi"

ENV C_FORCE_ROOT=1

COPY ./app /app
WORKDIR /app

ENV PYTHONPATH=/app

COPY ./app/worker-start.sh /worker-start.sh

RUN chmod +x /worker-start.sh

CMD ["sh", "/worker-start.sh"]
