"""The fixed sample recipes for "What can I cook?" (S2-05).

Recipes are plain data in code, not a database table. Amounts are whole
packages, matched by barcode against the pantry.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    barcode: str
    name: str
    needed: int  # packages


@dataclass(frozen=True)
class Recipe:
    name: str
    ingredients: tuple[Ingredient, ...]


SPAGHETTI = "8076800195057"
POLPA = "8005110170324"
PESTO = "8076809513753"
MOZZARELLA = "8000430133035"

RECIPES: tuple[Recipe, ...] = (
    Recipe(
        "Spaghetti with tomato",
        (
            Ingredient(SPAGHETTI, "Spaghetti", 1),
            Ingredient(POLPA, "Polpa di pomodoro", 2),
        ),
    ),
    Recipe(
        "Pesto pasta",
        (
            Ingredient(SPAGHETTI, "Spaghetti", 1),
            Ingredient(PESTO, "Barilla Pesto", 1),
        ),
    ),
    Recipe(
        "Tomato and mozzarella pasta",
        (
            Ingredient(SPAGHETTI, "Spaghetti", 1),
            Ingredient(POLPA, "Polpa di pomodoro", 1),
            Ingredient(MOZZARELLA, "Mozzarella", 1),
        ),
    ),
)
