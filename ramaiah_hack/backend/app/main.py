from __future__ import annotations

from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.state import AppState
from routes.dashboard import router as dashboard_router
from routes.simulation import router as simulation_router
from routes.system import router as system_router
from routes.upload import router as upload_router
from routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = AppState()
    state.load_on_startup()
    app.state.core = state
    yield


app = FastAPI(
    title="Hedge Fund Risk Modeling System",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    # Demo-friendly error payload (keeps frontend from hard-crashing on opaque 500s)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "trace": traceback.format_exc().splitlines()[-40:]},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(dashboard_router)
app.include_router(simulation_router)
app.include_router(upload_router)
app.include_router(admin_router)

