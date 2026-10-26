# Inventory Management API

FastAPI, SQLAlchemy 2.0, MySQL, Pydantic v2 and Alembic, using a layered architecture with JWT authentication and role-based access control.

This version adds pagination, filtering, sorting and search for products, categories, suppliers and users.

## Project Structure


app/
  api/
    deps.py                 authentication, role checks, pagination and filter dependencies, service providers
    routers/                HTTP layer only: auth, users, categories, suppliers, products
  core/                     settings, security (Argon2 and JWT), exceptions
  db/                       declarative base and session
  models/                   SQLAlchemy models
  repositories/
    base.py                 shared pagination helper and safe LIKE helper
    *_repository.py         query building and database access
  schemas/
    query.py                PaginationParams, Page[T], SortOrder, search normalisation
    product.py              ProductFilters, ProductSortField, request and response schemas
  services/                 business rules and transactions
alembic/versions/           0001 schema, 0002 query indexes
scripts/seed_data.py        demo users, categories, suppliers and 60 products
tests/                      pytest suite (69 tests, runs on in-memory SQLite)
postman_collection.json
```

## Setup

1. Create the database: run `setup_database.sql` in MySQL.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` and `SECRET_KEY`.
3. Install dependencies: `pip install -r requirements.txt`
4. Apply migrations: `alembic upgrade head`
5. Load demo data: `python -m scripts.seed_data`
6. Start the server: `uvicorn app.main:app --reload`

`run.bat` (Windows) and `run.sh` (Linux/macOS) perform steps 3 to 6 and create `.env` on first run.

Swagger UI is at `http://127.0.0.1:8000/docs`.

Demo accounts created by the seed script:

| Username | Password | Role |
|----------|----------|------|
| admin | Admin12345 | admin |
| manager | Manager12345 | manager |
| employee | Employee12345 | employee |

## Access Control

| Action | admin | manager | employee |
|--------|:-----:|:-------:|:--------:|
| List, search, filter, view products, categories, suppliers | yes | yes | yes |
| Create and update products, categories, suppliers | yes | yes | no |
| Delete products, categories, suppliers | yes | no | no |
| List and manage users | yes | no | no |

Every listing endpoint requires a valid access token. Pagination, filtering and search never bypass these checks.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/products` | Paginated listing with filters and sorting |
| GET | `/api/v1/products/search` | Search by name, SKU or description (`q` required) |
| GET | `/api/v1/products/low-stock` | Active products where `quantity <= reorder_level` |
| GET | `/api/v1/products/{id}` | Single product |
| POST / PUT / PATCH / DELETE | `/api/v1/products[/{id}]` | Create, update, delete |
| GET | `/api/v1/categories` | Paginated list, `search`, `is_active` |
| GET | `/api/v1/categories/{id}/products` | Paginated products of a category |
| GET | `/api/v1/suppliers` | Paginated list, `search`, `is_active` |
| GET | `/api/v1/suppliers/{id}/products` | Paginated products of a supplier |
| GET | `/api/v1/users` | Admin only. Paginated, `search`, `role`, `is_active` |
| POST | `/api/v1/auth/register`, `/login`, `/refresh`, `/logout` | Authentication |

### Common query parameters

| Parameter | Default | Rules |
|-----------|---------|-------|
| `page` | 1 | integer >= 1 |
| `page_size` | 10 | integer from 1 to 100 |

Invalid values return `422`. A page beyond the last page returns `200` with an empty `items` list and the real `total`.

### Product filters (`/products`, `/products/search`, `/products/low-stock`)

| Parameter | Description |
|-----------|-------------|
| `category_id`, `supplier_id` | Exact match |
| `min_price`, `max_price` | Inclusive price range |
| `min_quantity`, `max_quantity` | Inclusive stock range |
| `is_active` | `true` or `false` |
| `needs_restock` | `true`: `quantity <= reorder_level`, `false`: above it |
| `search` | Partial match on name, SKU and description |
| `sort_by` | `name`, `price`, `quantity`, `created_at`, `updated_at` |
| `sort_order` | `asc` (default) or `desc` |

`min_*` greater than `max_*` returns `422`. Filters can be combined freely. `/products/search` takes the term in `q` (required, 1 to 200 characters, not blank). `/products/low-stock` forces `needs_restock=true`, defaults to active products and sorts by `quantity` unless `sort_by` is given.

The category and supplier product routes accept the same filters except the one fixed by the path.

### Paginated response

```json
{
  "items": [
    {
      "id": 1,
      "name": "Gadget 001",
      "sku": "SKU-0001",
      "description": "Gadget model 1 for everyday use",
      "price": 12.99,
      "quantity": 13,
      "reorder_level": 20,
      "needs_restock": true,
      "is_active": true,
      "category_id": 2,
      "supplier_id": 2,
      "category": {"id": 2, "name": "Furniture"},
      "supplier": {"id": 2, "name": "Globex Trading"},
      "created_at": "2026-06-25T10:00:00",
      "updated_at": "2026-06-25T10:00:00"
    }
  ],
  "total": 60,
  "page": 1,
  "page_size": 10,
  "total_pages": 6
}
```

## Examples

```
GET /api/v1/products?page=2&page_size=5
GET /api/v1/products?category_id=1&min_price=50&max_price=300&is_active=true
GET /api/v1/products?min_quantity=5&max_quantity=40&sort_by=quantity&sort_order=asc
GET /api/v1/products?category_id=1&supplier_id=2&sort_by=price&sort_order=desc&page=1&page_size=5
GET /api/v1/products/search?q=widg
GET /api/v1/products/search?q=sku-00&min_price=10&sort_by=name
GET /api/v1/products/low-stock?category_id=1&page_size=20
GET /api/v1/categories?search=elec&page=1&page_size=10
GET /api/v1/suppliers?search=acme&is_active=true
GET /api/v1/categories/1/products?sort_by=price
GET /api/v1/suppliers/1/products?needs_restock=true
```

cURL with a token:

```
curl -X POST http://127.0.0.1:8000/api/v1/auth/login -d "username=admin&password=Admin12345"
curl "http://127.0.0.1:8000/api/v1/products?page=1&page_size=5&sort_by=price&sort_order=desc" -H "Authorization: Bearer <access_token>"
```

## Design Notes

**Shared pagination.** `repositories/base.py::paginate` takes any filtered `select`, counts rows with `SELECT COUNT(*) FROM (<filtered query>)`, then applies `ORDER BY`, `OFFSET` and `LIMIT`. Products, categories, suppliers and users all use it, so counts always match the applied filters and only one page of rows is loaded.

**Sorting safety.** `sort_by` and `sort_order` are Enums, so anything outside the allowed list is rejected with `422` before reaching the repository. The repository maps each enum member to a SQLAlchemy column through a fixed dictionary. User input is never placed into SQL text. A secondary sort on `id` keeps pages stable when sort values tie.

**Search safety.** Search terms are bound parameters, never concatenated. `%`, `_` and the escape character are escaped, so they are matched literally. Blank or whitespace-only terms are ignored on listing endpoints and rejected with `422` on `/products/search`. Terms longer than 100 characters are rejected.

**Query count.** A product page needs two queries: the count and the page. Category and supplier are loaded in the same page query through `joinedload`, so there is no N+1 problem.

**Indexes** (migration `0002`):

| Index | Supports |
|-------|----------|
| `products.sku` (unique) | SKU lookup, duplicate check, SKU sorting |
| `products.name` | name sorting and prefix lookups |
| `products.price`, `products.quantity` | range filters and sorting |
| `products.created_at`, `products.updated_at` | date sorting |
| `products.category_id`, `products.supplier_id` | foreign key filters |
| `suppliers.name`, `suppliers.is_active` | supplier search and active filter |
| `categories.name` (unique) | category lookup and ordering |
| `users.role`, `users.username`, `users.email` | user filters and login |

`LIKE '%term%'` cannot use a normal B-tree index. For very large product tables, add a `FULLTEXT` index on name and description and switch the search to `MATCH ... AGAINST`.

## Authentication

Argon2 password hashing, short-lived JWT access tokens and rotating refresh tokens stored in the database. Reusing a revoked refresh token revokes every token of that user. Passwords need at least 8 characters with a letter and a digit.

## Testing

Automated tests:

```
pytest
```

The suite uses in-memory SQLite and covers: first and second page, page beyond the data, invalid page and page size, partial name and SKU search, wildcard and injection strings, every filter, combined filters, ascending and descending sorting on every field, unsupported sort fields, counts under filters, low-stock, category and supplier product routes, and role permissions.

Postman: import `postman_collection.json`, run one of the login requests (it stores the token automatically), then use the folders Pagination, Filtering, Search, Sorting and Low Stock and Relations.

