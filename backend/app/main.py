"""FastAPI application entry point for the LearnFlow auth service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth

app = FastAPI(
    title="LearnFlow Auth API",
    version="0.1.0",
    description="UC-1 authentication: registration, login, JWT issuance.",
)

# allow_credentials=True requires explicit origins (not "*") — the React client
# sends fetch with credentials:"include" (FR-10, httpOnly-cookie ready).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
