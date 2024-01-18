FROM python:3.10

WORKDIR /app/

# Install Poetry
RUN pip install poetry --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple && poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "poetry self add https://pypi.tuna.tsinghua.edu.cn/packages/a8/ea/1a6df188d97a2f762a92e6df8ce75e0d25e6caefaa3a079c2d4efae7d721/poetry_plugin_pypi_mirror-0.4.1-py3-none-any.whl#sha256=51d1fabd782e670bfeb66beaf821df462649d8f6147c7efb02d1c71fe3c17f7b"
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then POETRY_PYPI_MIRROR_URL=https://pypi.tuna.tsinghua.edu.cn/simple poetry install --no-root ; else POETRY_PYPI_MIRROR_URL=https://pypi.tuna.tsinghua.edu.cn/simple poetry install --no-root --only main ; fi"

COPY ./app /app

CMD ["poetry", "run", "python", "-m", "app.main" ]
