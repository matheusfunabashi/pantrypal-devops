import pytest

BARCODE = "3017620422003"
TARGET_PATH = f"/stock-targets/{BARCODE}"


def test_shortage_tracks_stock_and_survives_pantry_removal(client):
    added = client.post("/pantry", json={"barcode": BARCODE, "quantity": 1})
    assert added.status_code == 201
    item_path = f"/pantry/{added.json()['id']}"

    saved = client.put(TARGET_PATH, json={"target": 3})
    assert saved.status_code == 200
    target = {"barcode": BARCODE, "name": "Nutella", "target": 3}
    assert saved.json() == target
    assert client.get("/restock").json() == [target | {"quantity": 1, "missing": 2}]

    assert client.put(item_path, json={"quantity": 3}).status_code == 200
    assert client.get("/restock").json() == []

    assert client.delete(item_path).status_code == 204
    assert client.get("/restock").json() == [target | {"quantity": 0, "missing": 3}]

    updated = client.put(TARGET_PATH, json={"target": 4})
    assert updated.status_code == 200
    assert client.get("/restock").json() == [target | {"target": 4, "quantity": 0, "missing": 4}]

    cleared = client.delete(TARGET_PATH)
    assert cleared.status_code == 204
    assert cleared.content == b""
    assert client.delete(TARGET_PATH).status_code == 404
    assert client.get("/restock").json() == []


def test_requires_inventory_for_a_new_target(client):
    assert client.put(TARGET_PATH, json={"target": 3}).status_code == 404


@pytest.mark.parametrize("target", [0, 1000, "abc", "3", 1.5, True])
def test_rejects_invalid_minimum_stock(client, target):
    assert client.put(TARGET_PATH, json={"target": target}).status_code == 422


def test_shortages_sort_by_product_name(client, catalog):
    beans = "5000157024671"
    catalog.products[beans] = {"name": "Beans"}

    for barcode in (BARCODE, beans):
        assert client.post("/pantry", json={"barcode": barcode, "quantity": 1}).status_code == 201
        assert client.put(f"/stock-targets/{barcode}", json={"target": 2}).status_code == 200

    shortages = client.get("/restock").json()
    assert [row["barcode"] for row in shortages] == [beans, BARCODE]
