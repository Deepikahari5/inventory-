import pytest

PRODUCT = {"name": "New Item", "sku": "new-001", "price": "19.99", "quantity": 5, "category_id": 1}


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/products",
        "/api/v1/products/search?q=a",
        "/api/v1/products/low-stock",
        "/api/v1/categories",
        "/api/v1/suppliers",
        "/api/v1/users",
    ],
)
def test_endpoints_require_authentication(client, catalog, path):
    assert client.get(path).status_code == 401


def test_invalid_token_rejected(client, catalog):
    response = client.get("/api/v1/products", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401


def test_employee_can_read_but_not_write(client, employee_headers, catalog):
    assert client.get("/api/v1/products", headers=employee_headers).status_code == 200
    assert client.get("/api/v1/products/search", params={"q": "wid"}, headers=employee_headers).status_code == 200
    assert client.get("/api/v1/products/low-stock", headers=employee_headers).status_code == 200
    assert client.post("/api/v1/products", json=PRODUCT, headers=employee_headers).status_code == 403
    assert client.delete("/api/v1/products/1", headers=employee_headers).status_code == 403


def test_manager_can_create_and_update_but_not_delete(client, manager_headers, catalog):
    created = client.post(
        "/api/v1/products",
        json={**PRODUCT, "category_id": catalog["categories"][0].id},
        headers=manager_headers,
    )
    assert created.status_code == 201
    assert created.json()["sku"] == "NEW-001"
    product_id = created.json()["id"]
    assert client.patch(f"/api/v1/products/{product_id}", json={"quantity": 50}, headers=manager_headers).status_code == 200
    assert client.delete(f"/api/v1/products/{product_id}", headers=manager_headers).status_code == 403


def test_admin_can_delete(client, admin_headers, catalog):
    created = client.post(
        "/api/v1/products",
        json={**PRODUCT, "category_id": catalog["categories"][0].id},
        headers=admin_headers,
    )
    product_id = created.json()["id"]
    assert client.delete(f"/api/v1/products/{product_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/products/{product_id}", headers=admin_headers).status_code == 404


@pytest.mark.parametrize("fixture", ["manager_headers", "employee_headers"])
def test_user_listing_is_admin_only(client, request, fixture):
    headers = request.getfixturevalue(fixture)
    assert client.get("/api/v1/users", headers=headers).status_code == 403


def test_admin_can_list_users_with_filters(client, admin_headers, db):
    from tests.conftest import create_user
    from app.models import UserRole

    create_user(db, UserRole.employee, "alice")
    create_user(db, UserRole.manager, "bob")
    body = client.get("/api/v1/users", params={"role": "employee"}, headers=admin_headers).json()
    assert body["total"] == 1
    body = client.get("/api/v1/users", params={"search": "bo"}, headers=admin_headers).json()
    assert body["total"] == 1


def test_pagination_respects_permissions_for_inactive_user(client, db, catalog):
    from tests.conftest import create_user, login
    from app.models import UserRole

    user = create_user(db, UserRole.employee, "temp")
    tokens = login(client, "temp")
    user.is_active = False
    db.commit()
    response = client.get("/api/v1/products", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 401


def test_product_crud_validation(client, manager_headers, catalog):
    category_id = catalog["categories"][0].id
    bad = client.post("/api/v1/products", json={**PRODUCT, "category_id": category_id, "price": "-5"}, headers=manager_headers)
    assert bad.status_code == 422
    missing = client.post("/api/v1/products", json={**PRODUCT, "category_id": 9999}, headers=manager_headers)
    assert missing.status_code == 404
    duplicate = client.post("/api/v1/products", json={**PRODUCT, "category_id": category_id, "sku": "SKU-001"}, headers=manager_headers)
    assert duplicate.status_code == 409


def test_category_with_products_cannot_be_deleted(client, admin_headers, catalog):
    category_id = catalog["categories"][0].id
    assert client.delete(f"/api/v1/categories/{category_id}", headers=admin_headers).status_code == 409
