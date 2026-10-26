from fastapi import APIRouter, FastAPI

from app.api.routers import auth, categories, products, suppliers, users
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="3.0.0",
    description="Inventory Management API with pagination, filtering, sorting and search.",
)

register_exception_handlers(app)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(suppliers.router)
api_router.include_router(products.router)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
