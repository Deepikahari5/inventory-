from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    computed_field,
    field_validator,
    model_validator,
)

from app.core.exceptions import UnprocessableError
from app.schemas.category import CategoryBrief
from app.schemas.query import SortOrder
from app.schemas.supplier import SupplierBrief

JsonDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]

SKU_PATTERN = r"^[A-Za-z0-9._-]+$"


class ProductSortField(str, Enum):
    name = "name"
    price = "price"
    quantity = "quantity"
    created_at = "created_at"
    updated_at = "updated_at"


@dataclass(frozen=True)
class ProductFilters:
    category_id: int | None = None
    supplier_id: int | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    min_quantity: int | None = None
    max_quantity: int | None = None
    is_active: bool | None = None
    needs_restock: bool | None = None
    search: str | None = None
    sort_by: ProductSortField | None = None
    sort_order: SortOrder = SortOrder.asc

    def validated(self) -> "ProductFilters":
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise UnprocessableError("min_price cannot be greater than max_price")
        if (
            self.min_quantity is not None
            and self.max_quantity is not None
            and self.min_quantity > self.max_quantity
        ):
            raise UnprocessableError("min_quantity cannot be greater than max_quantity")
        return self


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    sku: str = Field(min_length=1, max_length=50, pattern=SKU_PATTERN)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)
    is_active: bool = True
    category_id: int = Field(ge=1)
    supplier_id: int | None = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.upper()


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    sku: str | None = Field(default=None, min_length=1, max_length=50, pattern=SKU_PATTERN)
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    category_id: int | None = Field(default=None, ge=1)
    supplier_id: int | None = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else value

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        required = {"name", "sku", "price", "quantity", "reorder_level", "is_active", "category_id"}
        for field in self.model_fields_set & required:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    description: str | None
    price: JsonDecimal
    quantity: int
    reorder_level: int
    is_active: bool
    category_id: int
    supplier_id: int | None
    category: CategoryBrief
    supplier: SupplierBrief | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def needs_restock(self) -> bool:
        return self.quantity <= self.reorder_level
