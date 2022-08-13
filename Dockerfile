FROM python:3.10-slim

RUN apt-get update \
    && apt-get install curl -y \
    && curl -sSL https://install.python-poetry.org | python - --version 1.1.13

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app/

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry config virtualenvs.create false && poetry install --no-root

COPY ./ /app
ENV PYTHONPATH=/app
