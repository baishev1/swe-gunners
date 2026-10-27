from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core import settings
from features import (
    admin,
    audit_log,
    auth,
    checkin,
    events,
    organizers,
    promo,
    support,
    ticket_types,
    venues,
)

from .lifespan import lifespan

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.IS_DEV_ENV else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.IS_DEV_ENV else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str


@app.get("/health", tags=["Health"], response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


app.include_router(events.routes.router, prefix="/api/v1")
app.include_router(auth.routes.router, prefix="/api/v1")
app.include_router(organizers.routes.router, prefix="/api/v1")
app.include_router(venues.routes.router, prefix="/api/v1")
app.include_router(ticket_types.routes.router, prefix="/api/v1")
app.include_router(support.routes.router, prefix="/api/v1")
app.include_router(checkin.routes.router, prefix="/api/v1")
app.include_router(promo.routes.router, prefix="/api/v1")
app.include_router(audit_log.routes.router, prefix="/api/v1")
app.include_router(admin.routes.router, prefix="/api/v1")
