from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import RequestIdMiddleware, TenancyMiddleware
from app.core.exceptions import register_exception_handlers
from app.modules.identity.routes import router as identity_router
from app.modules.cases.routes import router as cases_router
from app.modules.roster.routes import router as roster_router
from app.modules.ingestion.routes import router as ingestion_router
from app.modules.analytics.routes import router as analytics_router
from app.modules.wellbeing.routes import router as wellbeing_router
from app.modules.student.routes import router as student_router
from app.modules.faculty.routes import router as faculty_router
from app.modules.audit.routes import router as audit_router

app = FastAPI(
    title="DISHA API",
    description="DISHA — Student Early-Warning & Intervention Platform API",
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

# Exception Handlers
register_exception_handlers(app)

# Health endpoint
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "DISHA API",
        "version": "1.0.0",
        "environment": settings.DISHA_ENV
    }

# Register Module Routers
app.include_router(identity_router, prefix="/api/v1/identity", tags=["Identity"])
app.include_router(student_router, prefix="/api/v1/student", tags=["Student"])
app.include_router(faculty_router, prefix="/api/v1/faculty", tags=["Faculty"])
app.include_router(cases_router, prefix="/api/v1/cases", tags=["Cases"])
app.include_router(roster_router, prefix="/api/v1/roster", tags=["Roster"])
app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["Ingestion"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(wellbeing_router, prefix="/api/v1/wellbeing", tags=["Wellbeing"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit"])
