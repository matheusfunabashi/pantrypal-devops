"""What can I cook? (S2-05)

GET /recipes compares the fixed recipes in recipe_data.py with the pantry and
says which ones are ready and what is missing for the others. It only reads the
pantry, so it never changes stock, and it doesn't call Catalog.
"""

import re
import unicodedata
from collections.abc import Iterable
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import pantry
from app.db import get_session
from app.models import PantryItem
from app.recipe_data import RECIPES, Ingredient, Recipe

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


def normalize(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name.casefold())
    text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[^\W_]+", text))


def matches_name(product: str, ingredient: Ingredient) -> bool:
    words = product.split()
    if any(word in words for word in ingredient.exclude_words):
        return False
    return any(
        f" {normalize(name)} " in f" {product} " for name in (ingredient.name, *ingredient.aliases)
    )


def availability(recipes: Iterable[Recipe], items: Iterable[PantryItem]) -> list[RecipeOut]:
    """Match each recipe against the pantry. A product not in the pantry counts as 0."""
    stock = [(item.barcode, normalize(item.name_snapshot), item.quantity) for item in items]
    result = []
    for recipe in recipes:
        ingredients = []
        for ingredient in recipe.ingredients:
            have = sum(
                quantity
                for barcode, product, quantity in stock
                if barcode == ingredient.barcode or matches_name(product, ingredient)
            )
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
