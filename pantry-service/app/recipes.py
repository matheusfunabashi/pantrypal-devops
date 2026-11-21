"""What can I cook? (S2-05)

GET /recipes compares the fixed recipes in recipe_data.py with the pantry and
says which ones are ready and what is missing for the others. It only reads the
pantry, so it never changes stock, and it doesn't call Catalog.
"""

from collections.abc import Iterable
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import pantry
from app.db import get_session
from app.models import PantryItem
from app.recipe_data import RECIPES, Recipe

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


class IngredientOut(BaseModel):
    barcode: str
    name: str
    needed: int
    have: int
    missing: int


class RecipeOut(BaseModel):
    name: str
    ready: bool
    ingredients: list[IngredientOut]


def availability(recipes: Iterable[Recipe], items: Iterable[PantryItem]) -> list[RecipeOut]:
    """Match each recipe against the pantry. A product not in the pantry counts as 0."""
    stock = {item.barcode: item.quantity for item in items}
    result = []
    for recipe in recipes:
        ingredients = []
        for ingredient in recipe.ingredients:
            have = stock.get(ingredient.barcode, 0)
            ingredients.append(
                IngredientOut(
                    barcode=ingredient.barcode,
                    name=ingredient.name,
                    needed=ingredient.needed,
                    have=have,
                    missing=max(ingredient.needed - have, 0),
                )
            )
        ready = all(ingredient.missing == 0 for ingredient in ingredients)
        result.append(RecipeOut(name=recipe.name, ready=ready, ingredients=ingredients))
    return result


@router.get("/recipes", response_model=list[RecipeOut])
def list_recipes(session: SessionDep) -> list[RecipeOut]:
    return availability(RECIPES, pantry.list_items(session))
