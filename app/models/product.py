from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.category import Category
from app.models.mixins import TimestampMixin
from app.models.supplier import Supplier


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_created_at", "created_at"),
        Index("ix_products_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)
    reorder_level: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    category: Mapped[Category] = relationship()
    supplier: Mapped[Supplier | None] = relationship()
