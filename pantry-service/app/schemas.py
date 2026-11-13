from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models import PantryItem

# strict=True: only real JSON integers count. "2", 2.0 and true are rejected
# with 422 instead of being quietly converted.
Quantity = Annotated[int, Field(strict=True, ge=1, le=999)]
# [0-9] rather than \d, so only the digits 0-9 are accepted.
Barcode = Annotated[str, Field(pattern=r"^[0-9]{8,14}$")]


class PantryItemCreate(BaseModel):
    """Body of POST /pantry."""

    barcode: Barcode
    quantity: Quantity


class PantryItemOut(BaseModel):
    """A pantry item as the API returns it."""

    id: int
    barcode: str
    quantity: int
    name: str
    brand: str | None
    image_url: str | None
    nutri_score: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, item: PantryItem) -> "PantryItemOut":
        # The database keeps the product details as *_snapshot columns.
        return cls(
            id=item.id,
            barcode=item.barcode,
            quantity=item.quantity,
            name=item.name_snapshot,
            brand=item.brand_snapshot,
            image_url=item.image_url_snapshot,
            nutri_score=item.nutri_score_snapshot,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
