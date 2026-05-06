from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.post("/reset-simulation")
def reset_simulation(request: Request):
    core = request.app.state.core
    core.replay.playing = False
    core.replay.portfolio.reset()
    core.replay.explain_logs.clear()
    core.replay.latest_signal.clear()
    # reset per-ticker cursors
    for t in core.replay.ticker_steps:
        core.replay.ticker_steps[t] = 0
    if core.replay.active_ticker:
        core.replay.step = 0
    return {"ok": True}

