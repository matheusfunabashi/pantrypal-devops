import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers pantry_items on Base.metadata)
from app.catalog_client import CatalogUnavailable, ProductNotFound, get_catalog
from app.db import Base
from app.main import app, get_session

NUTELLA = {
    "name": "Nutella",
    "brand": "Ferrero",
    "image_url": "https://example.com/nutella.jpg",
    "nutri_score": "e",
}


class FakeCatalog:
    """Stands in for the Catalog Service. Records every barcode it is asked for."""

    def __init__(self, products=None, error=None):
        self.products = products if products is not None else {}
        self.error = error
        self.calls = []

    def get_product(self, barcode):
        self.calls.append(barcode)
        if self.error is not None:
            raise self.error
        if barcode not in self.products:
            raise ProductNotFound(barcode)
        return self.products[barcode]


@pytest.fixture
def engine():
    # StaticPool: one shared connection, so every session sees the same in-memory database.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def catalog():
    return FakeCatalog(products={"3017620422003": NUTELLA})


@pytest.fixture
def client(engine, catalog):
    make_session = sessionmaker(bind=engine)

    def test_session():
        with make_session() as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[get_catalog] = lambda: catalog
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def catalog_down(client):
    app.dependency_overrides[get_catalog] = lambda: FakeCatalog(error=CatalogUnavailable())
    return client
