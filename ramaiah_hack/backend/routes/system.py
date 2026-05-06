from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/system-status")
def system_status(request: Request):
    core = request.app.state.core
    return {
        "ok": True,
        "assets_loaded": core.data.asset_count,
        "macro_loaded": core.data.macro_loaded,
        "simulation": core.replay.status(),
    }


@router.get("/available-assets")
def available_assets(request: Request):
    core = request.app.state.core
    return {"assets": core.data.available_assets()}

