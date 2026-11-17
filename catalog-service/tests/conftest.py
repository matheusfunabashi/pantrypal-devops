import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config
from app.db import Base


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def make_client(handler) -> httpx.Client:
    """An Open Food Facts client whose HTTP layer is a mock. No test calls the real API."""
    return httpx.Client(
        base_url=config.OFF_BASE_URL,
        headers={"User-Agent": config.OFF_USER_AGENT},
        timeout=config.OFF_TIMEOUT_SECONDS,
        transport=httpx.MockTransport(handler),
    )


NUTELLA = {
    "code": "3017620422003",
    "status": "success",
    "product": {
        "product_name": "  Nutella  ",
        "brands": "Ferrero, Nutella",
        "image_front_small_url": "https://images.example/nutella.jpg",
        "nutriscore_grade": "e",
    },
}
