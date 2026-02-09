"""FastAPI application for ClarityCheck."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

from contextlib import asynccontextmanager
from backend.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

from backend.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Document sanitization for assistive technology compliance",
    version=settings.VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"name": "ClarityCheck API", "status": "healthy", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
