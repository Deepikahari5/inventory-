from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import UnprocessableError

T = TypeVar("T")


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@dataclass(frozen=True)
class PaginationParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def build(cls, schema, items, total: int, params: PaginationParams):
        return cls(
            items=[schema.model_validate(item) for item in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=ceil(total / params.page_size) if total else 0,
        )


def normalize_search(value: str | None) -> str | None:
    if value is None:
        return None
    if "\x00" in value:
        raise UnprocessableError("Search value contains invalid characters")
    cleaned = " ".join(value.split())
    if not cleaned:
        return None
    if len(cleaned) > get_settings().max_search_length:
        raise UnprocessableError(
            f"Search value must not exceed {get_settings().max_search_length} characters"
        )
    return cleaned
