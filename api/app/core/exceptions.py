from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

class DishaBaseException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class EntityNotFoundError(DishaBaseException):
    def __init__(self, entity: str, identifier: str):
        super().__init__(f"{entity} with identifier '{identifier}' not found", 404)

class PermissionDeniedError(DishaBaseException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(DishaBaseException)
    async def disha_exception_handler(request: Request, exc: DishaBaseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "status_code": exc.status_code}
        )
