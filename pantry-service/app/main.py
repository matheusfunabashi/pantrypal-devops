import logging
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import config, pantry
from app.catalog_client import Catalog, CatalogUnavailable, ProductNotFound, get_catalog
from app.db import get_session as get_session
from app.logging_middleware import RequestLogMiddleware
from app.recipes import router as recipes_router
from app.restock import router as restock_router
from app.schemas import PantryItemCreate, PantryItemOut, PantryItemUpdate

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)

app = FastAPI(title="Pantry Service")
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(restock_router)


# Annotated dependencies (FastAPI's recommended style): routes ask for a session
# or a catalog by type, and tests swap them with app.dependency_overrides.
SessionDep = Annotated[Session, Depends(get_session)]
CatalogDep = Annotated[Catalog, Depends(get_catalog)]


@app.get("/health")
def health() -> dict[str, str]:
    # Shallow on purpose (decision D9): no database query.
    return {"status": "ok", "service": "pantry"}


@app.get("/pantry", response_model=list[PantryItemOut])
def list_pantry(session: SessionDep) -> list[PantryItemOut]:
    return [PantryItemOut.from_model(item) for item in pantry.list_items(session)]


@app.get("/pantry/{item_id}", response_model=PantryItemOut)
def get_pantry_item(item_id: int, session: SessionDep) -> PantryItemOut:
    try:
        item = pantry.get_item(session, item_id)
    except pantry.ItemNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found") from None
    return PantryItemOut.from_model(item)


@app.post("/pantry", response_model=PantryItemOut, status_code=status.HTTP_201_CREATED)
def add_pantry_item(
    body: PantryItemCreate,
    response: Response,
    session: SessionDep,
    catalog: CatalogDep,
) -> PantryItemOut:
    try:
        item, created = pantry.add_item(session, body.barcode, body.quantity, catalog)
    except ProductNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found") from None
    except CatalogUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Product lookup is temporarily unavailable"
        ) from None
    except pantry.QuantityTooHigh:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Quantity cannot go above {pantry.MAX_QUANTITY}",
        ) from None
    # 201 for a new item, 200 when an existing barcode's quantity went up.
    if not created:
        response.status_code = status.HTTP_200_OK
    return PantryItemOut.from_model(item)


@app.put("/pantry/{item_id}", response_model=PantryItemOut)
def update_pantry_item(item_id: int, body: PantryItemUpdate, session: SessionDep) -> PantryItemOut:
    """Set the quantity. Doesn't call Catalog, so it works when Catalog is down."""
    try:
        item = pantry.set_quantity(session, item_id, body.quantity)
    except pantry.ItemNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found") from None
    return PantryItemOut.from_model(item)


@app.delete("/pantry/{item_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_pantry_item(item_id: int, session: SessionDep) -> Response:
    """Remove the item. 204 with no body. Doesn't call Catalog either."""
    try:
        pantry.delete_item(session, item_id)
    except pantry.ItemNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


app.include_router(recipes_router)
