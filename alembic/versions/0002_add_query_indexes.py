"""add indexes for searching, filtering and sorting

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-23
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_users_role", "users", ["role"]),
    ("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"]),
    ("ix_suppliers_name", "suppliers", ["name"]),
    ("ix_suppliers_is_active", "suppliers", ["is_active"]),
    ("ix_products_name", "products", ["name"]),
    ("ix_products_price", "products", ["price"]),
    ("ix_products_quantity", "products", ["quantity"]),
    ("ix_products_category_id", "products", ["category_id"]),
    ("ix_products_supplier_id", "products", ["supplier_id"]),
    ("ix_products_created_at", "products", ["created_at"]),
    ("ix_products_updated_at", "products", ["updated_at"]),
]


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table)
