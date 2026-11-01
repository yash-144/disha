from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any


class DishaBaseException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class EntityNotFoundError(DishaBaseException):
    def __init__(self, entity: str, identifier: str):
        super().__init__(f"{entity} with identifier '{identifier}' not found", 404)


class PermissionDeniedError(DishaBaseException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class ConcurrencyConflictError(DishaBaseException):
    def __init__(
        self,
        message: str = "Resource has been modified concurrently by another transaction (version conflict)",
    ):
        super().__init__(message, 409)


class StateTransitionError(DishaBaseException):
    def __init__(self, from_state: str, to_state: str, reason: str = ""):
        msg = f"Invalid state transition from '{from_state}' to '{to_state}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, 422)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(DishaBaseException)
    async def disha_exception_handler(request: Request, exc: DishaBaseException):
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
        }
        if request_id:
            content["request_id"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )
