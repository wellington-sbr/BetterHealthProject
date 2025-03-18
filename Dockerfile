FROM python:3.13-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock .

COPY . .

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000

CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]