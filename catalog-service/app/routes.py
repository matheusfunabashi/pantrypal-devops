from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import off_client, products
from app.db import get_engine

router = APIRouter()


class ProductOut(BaseModel):
    barcode: str
    name: str
    brand: str | None
    image_url: str | None
    nutri_score: str | None
    source: str


def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session


@lru_cache
def get_off_http_client() -> httpx.Client:
    return off_client.build_client()


@router.get("/products/{barcode}", response_model=ProductOut)
def get_product(
    barcode: str,
    session: Annotated[Session, Depends(get_session)],
    client: Annotated[httpx.Client, Depends(get_off_http_client)],
) -> dict:
    try:
        return products.get_product(
            session, barcode, lambda code: off_client.fetch_product(client, code)
        )
    except products.InvalidBarcode:
        raise HTTPException(422, "Barcode must be 8 to 14 digits") from None
    except off_client.ProductNotFound:
        raise HTTPException(404, "Product not found") from None
    except off_client.CatalogUnavailable:
        raise HTTPException(503, "Product lookup is temporarily unavailable") from None
