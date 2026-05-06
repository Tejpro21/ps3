from __future__ import annotations

from fastapi import APIRouter, Request

from utils.json_sanitize import sanitize


router = APIRouter()


@router.get("/dashboard-data")
def dashboard_data(request: Request):
    core = request.app.state.core
    return sanitize(core.replay.dashboard_snapshot())


@router.get("/trade-logs")
def trade_logs(request: Request):
    core = request.app.state.core
    return sanitize({"trades": core.replay.trade_logs()})


@router.get("/portfolio-state")
def portfolio_state(request: Request):
    core = request.app.state.core
    return sanitize(core.replay.portfolio_state())


@router.get("/performance-metrics")
def performance_metrics(request: Request):
    core = request.app.state.core
    return sanitize(core.replay.performance_metrics())

