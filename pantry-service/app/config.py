import os

# Placeholder defaults for local development. Real values come from docker-compose / .env.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",") if o.strip()]

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_NAME = os.getenv("DB_NAME", "pantry_db")
DB_USER = os.getenv("DB_USER", "pantry_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
