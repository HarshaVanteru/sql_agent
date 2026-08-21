FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]