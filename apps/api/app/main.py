from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .db import engine
from .seed import seed_capabilities
from .config import settings
from sqlalchemy import text
from .db import SessionLocal
from .services.redis_queue import redis_client
from neo4j import AsyncGraphDatabase
from .api.v1.routes import router as api_router
from .api.v1.graph import router as graph_router
from .api.v1.evidence import router as evidence_router
from .api.v1.opportunities import router as opportunities_router
from .api.v1.reasoning import router as reasoning_router
from .api.v1.paths import router as paths_router
from .api.v1.graph_reasoning import router as graph_reasoning_router
from .api.v1.scenarios import router as scenarios_router
from .api.v1.simulation import router as simulation_router
from .api.v1.intelligence import router as intelligence_router
from .api.v1.relations import router as relations_router
from .api.v1.civilizational_opportunities import router as civilizational_opportunities_router
from .api.v1.opportunity_review import router as opportunity_review_router
from .api.v1.outbox import router as outbox_router
from .api.v1.profiles import router as profiles_router
from .api.v1.logistics import router as logistics_router
from .api.v1.value_chain import router as value_chain_router
from .api.v1.outreach import router as outreach_router

app = FastAPI(title="Civilizational Intelligence Network API", version="2.0.0")

origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(reasoning_router, prefix="/api/v1")
app.include_router(paths_router, prefix="/api/v1")
app.include_router(graph_reasoning_router, prefix="/api/v1")
app.include_router(scenarios_router, prefix="/api/v1")
app.include_router(simulation_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(relations_router, prefix="/api/v1")
app.include_router(civilizational_opportunities_router, prefix="/api/v1")
app.include_router(opportunity_review_router, prefix="/api/v1")
app.include_router(outbox_router, prefix="/api/v1")
app.include_router(profiles_router, prefix="/api/v1")
app.include_router(logistics_router, prefix="/api/v1")
app.include_router(value_chain_router, prefix="/api/v1")
app.include_router(outreach_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    await seed_capabilities()

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "environment": settings.app_environment}

@app.get("/health/ready")
async def readiness():
    checks = {}
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            checks["postgres"] = "ok"

        redis = redis_client()
        try:
            await redis.ping()
            checks["redis"] = "ok"
        finally:
            await redis.aclose()

        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        try:
            await driver.verify_connectivity()
            checks["neo4j"] = "ok"
        finally:
            await driver.close()

        return {"status": "ready", "checks": checks}
    except Exception as exc:
        checks["error"] = type(exc).__name__
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": checks},
        )
from .api.v1.client_intelligence import router as client_intelligence_router
app.include_router(client_intelligence_router, prefix='/api/v1')
