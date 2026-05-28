from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.admin_routes import router as admin_router
from .api.auth_routes import router as auth_router
from .api.live_routes import router as live_router
from .api.routes import router
from .config import settings

_LOCAL_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

_cors_origins = list(dict.fromkeys(_LOCAL_DEV_ORIGINS + settings.cors_origins))

app = FastAPI(title="MeetIQ (Phase 5)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(live_router)
