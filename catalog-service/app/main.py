import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.logging_middleware import RequestLogMiddleware

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)

app = FastAPI(title="Catalog Service")
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "catalog"}
