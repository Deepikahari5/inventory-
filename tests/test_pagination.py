import pytest

URL = "/api/v1/products"


def test_first_page_defaults(client, admin_headers, catalog):
    body = client.get(URL, headers=admin_headers).json()
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total"] == 25
    assert body["total_pages"] == 3
    assert len(body["items"]) == 10


def test_second_page_has_different_items(client, admin_headers, catalog):
    first = client.get(URL, headers=admin_headers).json()
    second = client.get(URL, params={"page": 2}, headers=admin_headers).json()
    assert second["page"] == 2
    assert len(second["items"]) == 10
    assert not {p["id"] for p in first["items"]} & {p["id"] for p in second["items"]}


def test_last_page_partial(client, admin_headers, catalog):
    body = client.get(URL, params={"page": 3}, headers=admin_headers).json()
    assert len(body["items"]) == 5


def test_page_beyond_available_records(client, admin_headers, catalog):
    response = client.get(URL, params={"page": 100}, headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 25
    assert body["total_pages"] == 3


@pytest.mark.parametrize("params", [{"page_size": 0}, {"page_size": 101}, {"page_size": -5}, {"page": 0}, {"page": -1}, {"page": "abc"}])
def test_invalid_pagination_rejected(client, admin_headers, catalog, params):
    assert client.get(URL, params=params, headers=admin_headers).status_code == 422


def test_max_page_size_allowed(client, admin_headers, catalog):
    body = client.get(URL, params={"page_size": 100}, headers=admin_headers).json()
    assert len(body["items"]) == 25
    assert body["total_pages"] == 1


def test_empty_result_has_zero_pages(client, admin_headers, catalog):
    body = client.get(URL, params={"min_price": 100000}, headers=admin_headers).json()
    assert body["total"] == 0
    assert body["total_pages"] == 0
    assert body["items"] == []


def test_categories_pagination(client, admin_headers, catalog):
    body = client.get("/api/v1/categories", params={"page_size": 1}, headers=admin_headers).json()
    assert body["total"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 1


def test_suppliers_pagination(client, admin_headers, catalog):
    body = client.get("/api/v1/suppliers", params={"page_size": 2}, headers=admin_headers).json()
    assert body["total"] == 3
    assert body["total_pages"] == 2


def test_users_pagination(client, admin_headers):
    body = client.get("/api/v1/users", params={"page_size": 5}, headers=admin_headers).json()
    assert body["total"] == 1
    assert body["page_size"] == 5
    assert client.get("/api/v1/users", params={"page_size": 500}, headers=admin_headers).status_code == 422
