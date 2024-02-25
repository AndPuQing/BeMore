FROM python:3.10

WORKDIR /app/

# Install Poetry
RUN pip install poetry --no-cache-dir && poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi
RUN poetry run python -m pip install --no-use-pep517 rectools[lightfm]

COPY ./app /app

CMD ["poetry", "run", "python", "-m", "app.main" ]
