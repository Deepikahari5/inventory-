URL = "/api/v1/products"


def names(body):
    return [item["name"] for item in body["items"]]


def get(client, headers, path=URL, **params):
    params.setdefault("page_size", 100)
    return client.get(path, params=params, headers=headers)


def test_filter_by_category(client, admin_headers, catalog):
    category_id = catalog["categories"][0].id
    body = get(client, admin_headers, category_id=category_id).json()
    assert body["total"] == 12
    assert all(item["category_id"] == category_id for item in body["items"])


def test_filter_by_supplier(client, admin_headers, catalog):
    supplier_id = catalog["suppliers"][1].id
    body = get(client, admin_headers, supplier_id=supplier_id).json()
    assert body["total"] == 8
    assert all(item["supplier_id"] == supplier_id for item in body["items"])


def test_filter_by_price_range(client, admin_headers, catalog):
    body = get(client, admin_headers, min_price=100, max_price=200).json()
    assert body["total"] == 11
    assert all(100 <= item["price"] <= 200 for item in body["items"])


def test_filter_by_quantity_range(client, admin_headers, catalog):
    body = get(client, admin_headers, min_quantity=20, max_quantity=40).json()
    assert body["total"] == 11


def test_filter_by_active_status(client, admin_headers, catalog):
    assert get(client, admin_headers, is_active="false").json()["total"] == 5
    assert get(client, admin_headers, is_active="true").json()["total"] == 20


def test_filter_needs_restock(client, admin_headers, catalog):
    assert get(client, admin_headers, needs_restock="true").json()["total"] == 10
    assert get(client, admin_headers, needs_restock="false").json()["total"] == 15


def test_combined_filters(client, admin_headers, catalog):
    category_id = catalog["categories"][0].id
    body = get(client, admin_headers, category_id=category_id, min_price=100, max_price=200).json()
    assert body["total"] == 6
    paged = get(
        client,
        admin_headers,
        category_id=category_id,
        min_price=100,
        max_price=200,
        page_size=4,
        page=2,
        sort_by="price",
        sort_order="desc",
    ).json()
    assert paged["total"] == 6
    assert paged["total_pages"] == 2
    assert len(paged["items"]) == 2
    assert [item["price"] for item in paged["items"]] == [120, 100]


def test_totals_reflect_filters(client, admin_headers, catalog):
    unfiltered = get(client, admin_headers).json()["total"]
    filtered = get(client, admin_headers, category_id=catalog["categories"][1].id).json()["total"]
    assert unfiltered == 25
    assert filtered == 13


def test_inverted_ranges_rejected(client, admin_headers, catalog):
    assert get(client, admin_headers, min_price=50, max_price=10).status_code == 422
    assert get(client, admin_headers, min_quantity=50, max_quantity=10).status_code == 422


def test_negative_filter_values_rejected(client, admin_headers, catalog):
    assert get(client, admin_headers, min_price=-1).status_code == 422
    assert get(client, admin_headers, category_id=0).status_code == 422


def test_search_partial_name(client, admin_headers, catalog):
    body = get(client, admin_headers, "/api/v1/products/search", q="widget").json()
    assert body["total"] == 12
    assert all("Widget" in name for name in names(body))


def test_search_partial_sku(client, admin_headers, catalog):
    body = get(client, admin_headers, "/api/v1/products/search", q="sku-01").json()
    assert body["total"] == 10


def test_search_description(client, admin_headers, catalog):
    body = get(client, admin_headers, "/api/v1/products/search", q="item 7").json()
    assert body["total"] == 1


def test_search_wildcards_are_literal(client, admin_headers, catalog):
    assert get(client, admin_headers, "/api/v1/products/search", q="%").json()["total"] == 0
    assert get(client, admin_headers, "/api/v1/products/search", q="_").json()["total"] == 0


def test_search_blank_values_rejected(client, admin_headers, catalog):
    assert get(client, admin_headers, "/api/v1/products/search", q="").status_code == 422
    assert get(client, admin_headers, "/api/v1/products/search", q="   ").status_code == 422
    assert get(client, admin_headers, "/api/v1/products/search").status_code == 422
    assert get(client, admin_headers, "/api/v1/products/search", q="x" * 201).status_code == 422


def test_search_injection_string_is_harmless(client, admin_headers, catalog):
    response = get(client, admin_headers, "/api/v1/products/search", q="'; DROP TABLE products; --")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert get(client, admin_headers).json()["total"] == 25


def test_listing_search_param_with_blank_is_ignored(client, admin_headers, catalog):
    assert get(client, admin_headers, search="   ").json()["total"] == 25


def test_search_combined_with_filters(client, admin_headers, catalog):
    body = get(client, admin_headers, "/api/v1/products/search", q="widget", max_price=100).json()
    assert body["total"] == 5


def test_sort_by_price(client, admin_headers, catalog):
    asc = get(client, admin_headers, sort_by="price", sort_order="asc").json()
    desc = get(client, admin_headers, sort_by="price", sort_order="desc").json()
    assert asc["items"][0]["price"] == 10
    assert desc["items"][0]["price"] == 250
    assert [i["price"] for i in asc["items"]] == sorted(i["price"] for i in asc["items"])


def test_sort_by_name(client, admin_headers, catalog):
    body = get(client, admin_headers, sort_by="name").json()
    assert names(body) == sorted(names(body))
    assert names(get(client, admin_headers, sort_by="name", sort_order="desc").json())[0] == "Widget 24"


def test_sort_by_quantity(client, admin_headers, catalog):
    body = get(client, admin_headers, sort_by="quantity", sort_order="desc").json()
    assert body["items"][0]["quantity"] == 50


def test_sort_by_created_and_updated(client, admin_headers, catalog):
    created = get(client, admin_headers, sort_by="created_at", sort_order="desc").json()
    updated = get(client, admin_headers, sort_by="updated_at", sort_order="asc").json()
    assert created["items"][0]["sku"] == "SKU-025"
    assert updated["items"][0]["sku"] == "SKU-001"


def test_sorting_is_stable_across_pages(client, admin_headers, catalog):
    seen = []
    for page in (1, 2, 3):
        body = client.get(URL, params={"sort_by": "name", "page": page, "page_size": 10}, headers=admin_headers).json()
        seen.extend(item["id"] for item in body["items"])
    assert len(seen) == len(set(seen)) == 25


def test_unsupported_sort_field_rejected(client, admin_headers, catalog):
    assert get(client, admin_headers, sort_by="password").status_code == 422
    assert get(client, admin_headers, sort_by="price; DROP TABLE products").status_code == 422
    assert get(client, admin_headers, sort_by="id").status_code == 422


def test_invalid_sort_order_rejected(client, admin_headers, catalog):
    assert get(client, admin_headers, sort_by="price", sort_order="sideways").status_code == 422


def test_low_stock_endpoint(client, admin_headers, catalog):
    body = get(client, admin_headers, "/api/v1/products/low-stock").json()
    assert body["total"] == 8
    assert all(item["needs_restock"] and item["is_active"] for item in body["items"])
    assert body["items"][0]["quantity"] == 2


def test_low_stock_supports_pagination_and_filters(client, admin_headers, catalog):
    body = get(client, admin_headers, "/api/v1/products/low-stock", page_size=3).json()
    assert body["total_pages"] == 3
    filtered = get(client, admin_headers, "/api/v1/products/low-stock", category_id=catalog["categories"][0].id).json()
    assert filtered["total"] == 4


def test_category_products(client, admin_headers, catalog):
    category_id = catalog["categories"][1].id
    body = get(client, admin_headers, f"/api/v1/categories/{category_id}/products").json()
    assert body["total"] == 13
    assert get(client, admin_headers, "/api/v1/categories/9999/products").status_code == 404


def test_supplier_products(client, admin_headers, catalog):
    supplier_id = catalog["suppliers"][0].id
    body = get(client, admin_headers, f"/api/v1/suppliers/{supplier_id}/products", sort_by="price").json()
    assert body["total"] == 17
    assert body["items"][0]["price"] == 10
    assert get(client, admin_headers, "/api/v1/suppliers/9999/products").status_code == 404


def test_category_search_and_filter(client, admin_headers, catalog):
    assert get(client, admin_headers, "/api/v1/categories", search="elec").json()["total"] == 1
    assert get(client, admin_headers, "/api/v1/categories", search="zzz").json()["total"] == 0
    assert get(client, admin_headers, "/api/v1/categories", is_active="false").json()["total"] == 0


def test_supplier_search_and_active_filter(client, admin_headers, catalog):
    assert get(client, admin_headers, "/api/v1/suppliers", search="acme").json()["total"] == 1
    assert get(client, admin_headers, "/api/v1/suppliers", is_active="true").json()["total"] == 2
    assert get(client, admin_headers, "/api/v1/suppliers", is_active="false").json()["total"] == 1


def test_response_includes_nested_relations(client, admin_headers, catalog):
    item = get(client, admin_headers, page_size=1).json()["items"][0]
    assert item["category"]["name"] in {"Electronics", "Furniture"}
    assert item["supplier"]["name"]
    assert "needs_restock" in item
