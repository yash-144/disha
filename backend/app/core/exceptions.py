from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class DishaBaseException(Exception):
    def __init__(self, message: str, code: str = "BAD_REQUEST", status_code: int = 400, details: list = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class EntityNotFoundError(DishaBaseException):
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            message=f"{entity} with identifier '{identifier}' not found",
            code="RESOURCE_NOT_FOUND",
            status_code=404
        )


class PermissionDeniedError(DishaBaseException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, code="PERMISSION_DENIED", status_code=403)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(DishaBaseException)
    async def disha_exception_handler(request: Request, exc: DishaBaseException):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": request_id,
                    "details": exc.details
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "Input validation error",
                    "request_id": request_id,
                    "details": exc.errors()
                }
            }
        )
