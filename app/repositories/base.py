from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.query import PaginationParams


def escape_like(value: str) -> str:
    return value.replace("/", "//").replace("%", "/%").replace("_", "/_")


def contains(column, term: str):
    return column.ilike(f"%{escape_like(term)}%", escape="/")


def paginate(
    session: Session,
    stmt: Select,
    params: PaginationParams,
    order_by=(),
    options=(),
):
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = session.scalar(count_stmt) or 0
    data_stmt = stmt.order_by(*order_by).options(*options).offset(params.offset).limit(params.page_size)
    items = list(session.scalars(data_stmt).unique())
    return items, total
