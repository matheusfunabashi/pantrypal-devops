from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import PantryItem, StockTarget
from app.schemas import Barcode, Quantity

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


class StockTargetIn(BaseModel):
    target: Quantity


class StockTargetOut(BaseModel):
    barcode: str
    name: str
    target: int


class Shortage(StockTargetOut):
    quantity: int
    missing: int


def shortages(targets: Iterable[StockTarget], items: Iterable[PantryItem]) -> list[Shortage]:
    """Calculate shortages from saved targets. A missing pantry row has zero units."""
    quantities = {item.barcode: item.quantity for item in items}
    rows = []
    for target in targets:
        quantity = quantities.get(target.barcode, 0)
        missing = target.target - quantity
        if missing > 0:
            rows.append(
                Shortage(
                    barcode=target.barcode,
                    name=target.name,
                    target=target.target,
                    quantity=quantity,
                    missing=missing,
                )
            )
    return sorted(rows, key=lambda row: (row.name.casefold(), row.barcode))


def _update_target(session: Session, barcode: str, target: int) -> StockTargetOut | None:
    result = session.execute(
        update(StockTarget)
        .where(StockTarget.barcode == barcode)
        .values(target=target, updated_at=datetime.now(UTC).replace(tzinfo=None))
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        return None
    name = session.scalar(select(StockTarget.name).where(StockTarget.barcode == barcode))
    response = StockTargetOut(barcode=barcode, name=name, target=target)
    session.commit()
    return response


@router.get("/restock", response_model=list[Shortage])
def list_shortages(session: SessionDep) -> list[Shortage]:
    rows = session.execute(
        select(StockTarget, PantryItem).outerjoin(
            PantryItem, PantryItem.barcode == StockTarget.barcode
        )
    ).all()
    return shortages(
        (target for target, _ in rows),
        (item for _, item in rows if item is not None),
    )


@router.put("/stock-targets/{barcode}", response_model=StockTargetOut)
def set_target(barcode: Barcode, body: StockTargetIn, session: SessionDep) -> StockTargetOut:
    existing = _update_target(session, barcode, body.target)
    if existing is not None:
        return existing

    name = session.scalar(select(PantryItem.name_snapshot).where(PantryItem.barcode == barcode))
    if name is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product is not in the pantry")

    session.add(StockTarget(barcode=barcode, name=name, target=body.target))
    try:
        session.commit()
    except IntegrityError:
        # Another request may have created the target since the UPDATE above.
        session.rollback()
        existing = _update_target(session, barcode, body.target)
        if existing is None:
            raise
        return existing
    return StockTargetOut(barcode=barcode, name=name, target=body.target)


@router.delete(
    "/stock-targets/{barcode}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def clear_target(barcode: Barcode, session: SessionDep) -> Response:
    result = session.execute(
        delete(StockTarget)
        .where(StockTarget.barcode == barcode)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stock target not found")
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
