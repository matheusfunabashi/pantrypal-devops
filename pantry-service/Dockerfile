FROM python:3.12.16-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini start.sh ./
COPY migrations ./migrations

USER appuser

EXPOSE 8000

# start.sh runs the migrations (with retries), then uvicorn.
CMD ["./start.sh"]
