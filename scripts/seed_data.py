from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.core.timeutil import utcnow
from app.db.session import SessionLocal
from app.models import Category, Product, Supplier, User, UserRole

USERS = [
    ("admin", "admin@example.com", "Admin12345", UserRole.admin),
    ("manager", "manager@example.com", "Manager12345", UserRole.manager),
    ("employee", "employee@example.com", "Employee12345", UserRole.employee),
]

CATEGORIES = ["Electronics", "Furniture", "Stationery", "Hardware", "Kitchen"]

SUPPLIERS = [
    ("Acme Supplies", True),
    ("Globex Trading", True),
    ("Initech Wholesale", False),
    ("Umbrella Distribution", True),
]

NOUNS = ["Widget", "Gadget", "Cable", "Lamp", "Chair", "Notebook", "Drill", "Mixer", "Monitor", "Stapler"]


def seed() -> None:
    db = SessionLocal()
    try:
        for username, email, password, role in USERS:
            if not db.scalar(select(User).where(User.username == username)):
                db.add(User(username=username, email=email, hashed_password=hash_password(password), role=role))
        db.commit()

        if db.scalar(select(Category).limit(1)):
            return

        categories = [Category(name=name) for name in CATEGORIES]
        suppliers = [Supplier(name=name, email=f"contact@{name.split()[0].lower()}.com", is_active=active) for name, active in SUPPLIERS]
        db.add_all(categories + suppliers)
        db.commit()

        start = utcnow() - timedelta(days=120)
        for i in range(1, 61):
            noun = NOUNS[i % len(NOUNS)]
            stamp = start + timedelta(days=i * 2)
            db.add(
                Product(
                    name=f"{noun} {i:03d}",
                    sku=f"SKU-{i:04d}",
                    description=f"{noun} model {i} for everyday use",
                    price=Decimal(5 + (i * 7) % 480) + Decimal("0.99"),
                    quantity=(i * 13) % 90,
                    reorder_level=20,
                    is_active=i % 7 != 0,
                    category_id=categories[i % len(categories)].id,
                    supplier_id=suppliers[i % len(suppliers)].id,
                    created_at=stamp,
                    updated_at=stamp,
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
