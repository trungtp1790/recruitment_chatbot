from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from .config import settings
from .db import create_pg_pool
from .intent import detect_intent, should_update_memory
from .job_service import search_jobs
from .llm_service import generate_reply
from .job_ingest import sync_jobs_from_web
from .memory_service import load_slot, update_slot
from .schemas import ChatRequest, ChatResponse, JobItem, MemorySlot

redis_client: Redis | None = None
pg_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global redis_client, pg_pool
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    pg_pool = await create_pg_pool()
    yield
    if redis_client:
        await redis_client.aclose()
    if pg_pool:
        await pg_pool.close()


app = FastAPI(title="Recruitment Chatbot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    payload: dict = {"status": "ok", "env": settings.app_env}
    if redis_client is not None:
        try:
            await redis_client.ping()
            payload["redis"] = "ok"
        except Exception:
            payload["redis"] = "error"
    if pg_pool is not None:
        try:
            async with pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            payload["postgres"] = "ok"
        except Exception:
            payload["postgres"] = "error"
    return payload


@app.post("/api/admin/jobs/sync")
async def admin_jobs_sync(x_sync_secret: str | None = Header(default=None, alias="X-Sync-Secret")) -> dict:
    """Kéo tin từ TopCV (và ghi chú ITviec/LinkedIn). Bảo vệ bằng SYNC_JOBS_SECRET nếu có."""
    if settings.sync_jobs_secret and x_sync_secret != settings.sync_jobs_secret:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Sync-Secret")
    if pg_pool is None:
        raise HTTPException(status_code=503, detail="Database not ready")
    return await sync_jobs_from_web(pg_pool)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if redis_client is None or pg_pool is None:
        raise RuntimeError("Dependencies are not initialized")

    intent = detect_intent(request.message)
    if should_update_memory(intent):
        slot = await update_slot(redis_client, request.session_id, request.message)
    else:
        slot = await load_slot(redis_client, request.session_id)

    if intent in ("off_topic", "bot_identity"):
        jobs: list[JobItem] = []
    else:
        jobs = await search_jobs(pg_pool, request.message, slot)

    reply = await generate_reply(request.message, jobs, slot, intent)

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        jobs=jobs,
        intent=intent,
        memory_updated=slot.model_dump(),
    )


@app.get("/api/jobs/search", response_model=list[JobItem])
async def jobs_search(
    q: str = Query(default=""),
    session_id: str | None = Query(default=None),
) -> list[JobItem]:
    if redis_client is None or pg_pool is None:
        raise RuntimeError("Dependencies are not initialized")
    slot = await load_slot(redis_client, session_id) if session_id else load_slot_fallback()
    return await search_jobs(pg_pool, q, slot)


def load_slot_fallback():
    return MemorySlot()
