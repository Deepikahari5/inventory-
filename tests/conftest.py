from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Category, Product, Supplier, User, UserRole

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

PASSWORD = "Passw0rd123"


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user(db, role: UserRole, username: str | None = None) -> User:
    name = username or role.value
    user = User(
        username=name,
        email=f"{name}@example.com",
        hashed_password=hash_password(PASSWORD),
        role=role,
    )
    db.add(user)
    db.commit()
    return user


def login(client, username: str) -> dict:
    response = client.post("/api/v1/auth/login", data={"username": username, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()


def headers_for(client, db, role: UserRole) -> dict:
    create_user(db, role)
    tokens = login(client, role.value)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def admin_headers(client, db):
    return headers_for(client, db, UserRole.admin)


@pytest.fixture
def manager_headers(client, db):
    return headers_for(client, db, UserRole.manager)


@pytest.fixture
def employee_headers(client, db):
    return headers_for(client, db, UserRole.employee)


@pytest.fixture
def catalog(db):
    categories = [Category(name="Electronics"), Category(name="Furniture")]
    suppliers = [
        Supplier(name="Acme Supplies", is_active=True),
        Supplier(name="Globex Trading", is_active=True),
        Supplier(name="Initech Wholesale", is_active=False),
    ]
    db.add_all(categories + suppliers)
    db.commit()
    base = datetime(2026, 1, 1)
    for i in range(1, 26):
        stamp = base + timedelta(days=i)
        db.add(
            Product(
                name=f"{'Widget' if i % 2 == 0 else 'Gadget'} {i:02d}",
                sku=f"SKU-{i:03d}",
                description=f"Description for item {i}",
                price=Decimal(10 * i),
                quantity=2 * i,
                reorder_level=20,
                is_active=i % 5 != 0,
                category_id=categories[i % 2].id,
                supplier_id=suppliers[1].id if i % 3 == 0 else suppliers[0].id,
                created_at=stamp,
                updated_at=stamp,
            )
        )
    db.commit()
    return {"categories": categories, "suppliers": suppliers}
