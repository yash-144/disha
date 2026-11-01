from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware, TenancyMiddleware
from app.core.exceptions import register_exception_handlers
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import Role
from app.core.database import db

# Module routers
from app.api.auth import router as auth_router
from app.api.counsellor import router as counsellor_router
from app.api.cases import router as cases_router
from app.api.interventions import router as interventions_router
from app.api.followups import router as followups_router
from app.api.notifications import router as notifications_router
from app.api.admin import router as admin_router
from app.modules.pulse.routes import router as pulse_router

setup_logging()

app = FastAPI(
    title=f"{settings.DISHA_APP_NAME} API",
    description="DISHA — Student Support, Academic Risk Prediction & Early Intervention CRM Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.DISHA_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TenancyMiddleware)

# Exception handlers
register_exception_handlers(app)

# Health endpoint
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": f"{settings.DISHA_APP_NAME} API",
        "version": "1.0.0",
        "environment": settings.DISHA_ENV,
        "database": "connected"
    }

# Audit verification endpoint
@app.get("/api/v1/audit/logs", tags=["Audit"])
async def get_audit_trail(
    current_user: dict = Depends(require_roles(Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN))
):
    with db._lock:
        return {
            "total_audit_events": len(db.audit_log),
            "latest_hash": db._last_audit_hash,
            "events": db.audit_log[-50:]
        }

# API Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(counsellor_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")
app.include_router(interventions_router, prefix="/api/v1")
app.include_router(followups_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(pulse_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.DISHA_API_HOST, port=settings.DISHA_API_PORT, reload=True)
