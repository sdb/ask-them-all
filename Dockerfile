# The builder image, used to build the virtual environment
FROM python:3.11-buster as builder

RUN pip install --no-cache-dir poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY . .

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-buster as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/askthemall ./askthemall
COPY --from=builder /app/css ./css
COPY --from=builder /app/main.py ./main.py
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

CMD ["python", "-m", "streamlit", "run", "main.py"]
