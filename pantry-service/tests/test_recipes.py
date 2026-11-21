"""S2-05 What can I cook?"""

import pytest

from app.catalog_client import CatalogUnavailable
from app.models import PantryItem
from app.recipe_data import MOZZARELLA, PESTO, POLPA, RECIPES, SPAGHETTI, Ingredient, Recipe
from app.recipes import availability

PASTA = Recipe("Pasta", (Ingredient(SPAGHETTI, "Spaghetti", 1), Ingredient(POLPA, "Polpa", 2)))


def item(barcode, quantity):
    return PantryItem(barcode=barcode, quantity=quantity, name_snapshot="from the pantry")


def ingredient(recipe, name):
    return next(row for row in recipe.ingredients if row.name == name)


def by_name(recipes):
    return {recipe["name"]: recipe for recipe in recipes}


# ---------------------------------------------------------------- availability()


def test_all_ingredients_present_is_ready():
    [recipe] = availability([PASTA], [item(SPAGHETTI, 1), item(POLPA, 2)])

    assert recipe.ready is True
    assert [row.missing for row in recipe.ingredients] == [0, 0]


def test_more_than_needed_is_still_ready_with_nothing_missing():
    [recipe] = availability([PASTA], [item(SPAGHETTI, 5), item(POLPA, 9)])

    assert recipe.ready is True
    assert ingredient(recipe, "Polpa").missing == 0


def test_one_package_short_is_missing_one():
    [recipe] = availability([PASTA], [item(SPAGHETTI, 1), item(POLPA, 1)])

    assert recipe.ready is False
    polpa = ingredient(recipe, "Polpa")
    assert (polpa.needed, polpa.have, polpa.missing) == (2, 1, 1)


def test_ingredient_not_in_the_pantry_has_zero():
    [recipe] = availability([PASTA], [item(SPAGHETTI, 1)])

    polpa = ingredient(recipe, "Polpa")
    assert (polpa.have, polpa.missing) == (0, 2)
    assert recipe.ready is False


def test_empty_pantry_makes_nothing():
    recipes = availability(RECIPES, [])

    assert [recipe.ready for recipe in recipes] == [False, False, False]


def test_ingredient_names_come_from_the_recipe_not_the_pantry():
    [recipe] = availability([PASTA], [item(SPAGHETTI, 1)])

    assert ingredient(recipe, "Spaghetti").name == "Spaghetti"


def test_recipe_data_matches_the_issue():
    assert [
        (recipe.name, [(i.barcode, i.needed) for i in recipe.ingredients]) for recipe in RECIPES
    ] == [
        ("Spaghetti with tomato", [(SPAGHETTI, 1), (POLPA, 2)]),
        ("Pesto pasta", [(SPAGHETTI, 1), (PESTO, 1)]),
        ("Tomato and mozzarella pasta", [(SPAGHETTI, 1), (POLPA, 1), (MOZZARELLA, 1)]),
    ]


# ---------------------------------------------------------------- GET /recipes


@pytest.fixture
def shop(catalog):
    """The catalog knows the four recipe products."""
    catalog.products.update(
        {
            SPAGHETTI: {"name": "Spaghetti Nº5"},
            POLPA: {"name": "Polpa di pomodoro"},
            PESTO: {"name": "Pesto alla Genovese"},
            MOZZARELLA: {"name": "Mozzarella"},
        }
    )
    return catalog


def add(client, barcode, quantity):
    response = client.post("/pantry", json={"barcode": barcode, "quantity": quantity})
    assert response.status_code in (200, 201)


def test_get_recipes_on_an_empty_pantry(client):
    response = client.get("/recipes")

    assert response.status_code == 200
    recipes = response.json()
    assert [recipe["name"] for recipe in recipes] == [
        "Spaghetti with tomato",
        "Pesto pasta",
        "Tomato and mozzarella pasta",
    ]
    assert all(recipe["ready"] is False for recipe in recipes)
    assert recipes[0]["ingredients"][0] == {
        "barcode": SPAGHETTI,
        "name": "Spaghetti",
        "needed": 1,
        "have": 0,
        "missing": 1,
    }


def test_the_example_from_the_issue(client, shop):
    """1 Spaghetti and 1 Pesto: Pesto pasta is ready, tomato pasta is missing 2 Polpa."""
    add(client, SPAGHETTI, 1)
    add(client, PESTO, 1)

    recipes = by_name(client.get("/recipes").json())
    assert recipes["Pesto pasta"]["ready"] is True
    tomato = recipes["Spaghetti with tomato"]
    assert tomato["ready"] is False
    assert [(i["name"], i["missing"]) for i in tomato["ingredients"] if i["missing"]] == [
        ("Polpa di pomodoro", 2)
    ]

    add(client, POLPA, 2)

    recipes = by_name(client.get("/recipes").json())
    assert recipes["Spaghetti with tomato"]["ready"] is True
    assert recipes["Tomato and mozzarella pasta"]["ready"] is False


def test_get_recipes_never_changes_stock(client, shop):
    add(client, SPAGHETTI, 3)
    add(client, POLPA, 2)
    before = client.get("/pantry").json()

    for _ in range(3):
        assert client.get("/recipes").status_code == 200

    assert client.get("/pantry").json() == before


def test_get_recipes_works_when_catalog_is_down(client, shop):
    """Stock is read from the pantry database only, so Catalog being down doesn't matter."""
    add(client, SPAGHETTI, 1)
    add(client, PESTO, 1)
    shop.error = CatalogUnavailable()

    response = client.get("/recipes")

    assert response.status_code == 200
    assert by_name(response.json())["Pesto pasta"]["ready"] is True
    assert shop.calls == [SPAGHETTI, PESTO]  # only the two additions asked Catalog


def test_alternative_products_update_all_recipes(client, shop):
    products = {
        "8076800195033": "Spaghettini N°3",
        "1111111111111": "Store brand PÉSTO alla Genovese",
        "2222222222222": "Organic chopped-tomatoes",
        "3333333333333": "Fresh mozzarella di bufala",
    }
    for barcode, name in products.items():
        shop.products[barcode] = {"name": name}
        add(client, barcode, 1)
    add(client, POLPA, 1)
    add(client, SPAGHETTI, 1)

    recipes = client.get("/recipes").json()
    assert all(recipe["ready"] for recipe in recipes)
    assert [i["have"] for i in recipes[0]["ingredients"]] == [2, 2]

    rows = client.get("/pantry").json()
    pasta = next(row for row in rows if row["barcode"] == "8076800195033")
    assert client.delete(f"/pantry/{pasta['id']}").status_code == 204
    assert client.get("/recipes").json()[0]["ingredients"][0]["have"] == 1


@pytest.mark.parametrize("name", ["Spaghetti sauce", "Spaghettissimo", "Spaghetti & meatballs"])
def test_similar_names_and_prepared_products_do_not_supply_pasta(name):
    product = PantryItem(barcode="11111111", name_snapshot=name, quantity=1)
    assert availability(RECIPES, [product])[0].ingredients[0].have == 0
