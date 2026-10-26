from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class AppError(Exception):
    status_code = 400
    detail = "Bad request"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Could not validate credentials"
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(AppError):
    status_code = 403
    detail = "You do not have permission to perform this action"


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    detail = "Resource conflict"


class UnprocessableError(AppError):
    status_code = 422
    detail = "Unprocessable request"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={"detail": "The operation conflicts with existing data"},
        )
