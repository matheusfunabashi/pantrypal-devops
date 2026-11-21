"""The fixed sample recipes for "What can I cook?" (S2-05).

Recipes are plain data in code, not a database table. Amounts are whole
packages. Each ingredient has a reference barcode and optional product-name variants.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    barcode: str
    name: str
    needed: int  # packages
    aliases: tuple[str, ...] = ()
    exclude_words: tuple[str, ...] = ()


@dataclass(frozen=True)
class Recipe:
    name: str
    ingredients: tuple[Ingredient, ...]


SPAGHETTI = "8076800195057"
POLPA = "8005110170324"
PESTO = "8076809513753"
MOZZARELLA = "8000430133035"

spaghetti = Ingredient(
    SPAGHETTI, "Spaghetti", 1, ("spaghettini",), ("sauce", "soup", "meatballs", "bolognese")
)
tomato_names = ("tomato pulp", "chopped tomatoes", "crushed tomatoes", "diced tomatoes")

RECIPES: tuple[Recipe, ...] = (
    Recipe(
        "Spaghetti with tomato",
        (
            spaghetti,
            Ingredient(POLPA, "Polpa di pomodoro", 2, tomato_names),
        ),
    ),
    Recipe(
        "Pesto pasta",
        (
            spaghetti,
            Ingredient(PESTO, "Pesto", 1, exclude_words=("chips", "crisps", "pizza", "pasta")),
        ),
    ),
    Recipe(
        "Tomato and mozzarella pasta",
        (
            spaghetti,
            Ingredient(POLPA, "Polpa di pomodoro", 1, tomato_names),
            Ingredient(MOZZARELLA, "Mozzarella", 1, exclude_words=("pizza", "sticks")),
        ),
    ),
)
