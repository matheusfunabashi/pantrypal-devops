import pytest

BARCODE = "3017620422003"


def test_list_is_empty_at_first(client):
    response = client.get("/pantry")

    assert response.status_code == 200
    assert response.json() == []


def test_post_new_item_returns_201_with_product_details(client):
    response = client.post("/pantry", json={"barcode": BARCODE, "quantity": 2})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "id",
        "barcode",
        "quantity",
        "name",
        "brand",
        "image_url",
        "nutri_score",
        "created_at",
        "updated_at",
    }
    assert body["barcode"] == BARCODE
    assert body["quantity"] == 2
    assert body["name"] == "Nutella"
    assert body["nutri_score"] == "e"


def test_post_existing_barcode_returns_200_and_increments(client, catalog):
    first = client.post("/pantry", json={"barcode": BARCODE, "quantity": 2}).json()

    response = client.post("/pantry", json={"barcode": BARCODE, "quantity": 2})

    assert response.status_code == 200
    assert response.json()["id"] == first["id"]
    assert response.json()["quantity"] == 4
    assert catalog.calls == [BARCODE]
    assert len(client.get("/pantry").json()) == 1


def test_get_item_by_id(client):
    created = client.post("/pantry", json={"barcode": BARCODE, "quantity": 1}).json()

    response = client.get(f"/pantry/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_item_returns_404(client):
    response = client.get("/pantry/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


@pytest.mark.parametrize("quantity", [0, -1, 1000, "abc", "2", 2.5, True, None])
def test_invalid_quantity_returns_422(client, quantity):
    response = client.post("/pantry", json={"barcode": BARCODE, "quantity": quantity})

    assert response.status_code == 422


@pytest.mark.parametrize("barcode", ["1234567", "123456789012345", "12345abc", "", 12345678])
def test_invalid_barcode_returns_422(client, barcode):
    response = client.post("/pantry", json={"barcode": barcode, "quantity": 1})

    assert response.status_code == 422


def test_total_above_999_returns_422(client):
    client.post("/pantry", json={"barcode": BARCODE, "quantity": 999})

    response = client.post("/pantry", json={"barcode": BARCODE, "quantity": 1})

    assert response.status_code == 422
    assert response.json() == {"detail": "Quantity cannot go above 999"}


def test_unknown_product_returns_404(client):
    response = client.post("/pantry", json={"barcode": "12345678", "quantity": 1})

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


def test_catalog_down_returns_503(catalog_down):
    response = catalog_down.post("/pantry", json={"barcode": BARCODE, "quantity": 1})

    assert response.status_code == 503
    assert response.json() == {"detail": "Product lookup is temporarily unavailable"}
