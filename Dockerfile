FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME='/usr/local'

RUN curl -sSL 'https://install.python-poetry.org' | python -

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry install

COPY . .

CMD ["python", "manage.py", "runserver"]
