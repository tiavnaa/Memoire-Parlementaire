from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import search_router, deputies_router, seances_router, legislatives_router, stats_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API d'exploration des archives parlementaires de Madagascar",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(deputies_router, prefix="/api/deputies", tags=["Deputies"])
app.include_router(seances_router, prefix="/api/seances", tags=["Seances"])
app.include_router(legislatives_router, prefix="/api/legislatives", tags=["Legislatives"])
app.include_router(stats_router, prefix="/api/stats", tags=["Statistics"])

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    from app.services.elasticsearch_service import es_service
    if es_service.es and es_service.es.ping():
        return {"status": "healthy", "elasticsearch": "connected"}
    return {"status": "unhealthy", "elasticsearch": "disconnected"}