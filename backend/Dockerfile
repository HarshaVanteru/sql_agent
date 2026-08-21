FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/backend

EXPOSE 10000

CMD ["sh", "-c", "alembic -c /app/backend/alembic.ini upgrade head && exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]