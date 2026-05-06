from __future__ import annotations

import json
from typing import Literal, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


router = APIRouter()


class StartSimulationRequest(BaseModel):
    action: Literal["play", "pause", "step_next", "step_prev", "set_speed", "set_active"] = "play"
    ticker: Optional[str] = None
    speed: Optional[float] = Field(default=None, ge=0.25, le=10.0)


@router.post("/start-simulation")
def start_simulation(body: StartSimulationRequest, request: Request):
    core = request.app.state.core
    core.replay.control(action=body.action, ticker=body.ticker, speed=body.speed)
    return {"ok": True, "simulation": core.replay.status()}


@router.get("/simulation-stream")
def simulation_stream(request: Request):
    core = request.app.state.core

    async def event_gen():
        # Server-Sent Events: frontend can keep one connection open
        async for evt in core.replay.sse_events():
            yield f"data: {json.dumps(evt)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")

