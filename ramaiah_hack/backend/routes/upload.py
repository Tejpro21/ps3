from __future__ import annotations

import os
from typing import Literal, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from utils.json_sanitize import sanitize


router = APIRouter()


class UploadResponse(BaseModel):
    ok: bool
    filename: str
    dataset_type: Literal["market", "macro"]


@router.post("/upload-dataset", response_model=UploadResponse)
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    dataset_type: Literal["market", "macro"] = "market",
    target_name: Optional[str] = None,
):
    """
    Upload a CSV and place it into ./datasets/ under an expected filename.
    This is for local hackathon demo UX; backend immediately reloads datasets.
    """
    core = request.app.state.core
    root = core.data.root_dir
    datasets_dir = os.path.join(root, "datasets")
    os.makedirs(datasets_dir, exist_ok=True)

    allowed = {
        "oil_dataset.csv",
        "equity_dataset.csv",
        "multi_asset_dataset.csv",
        "macro_dataset.csv",
    }
    out_name = (target_name or file.filename or "").strip()
    if out_name not in allowed:
        raise HTTPException(status_code=400, detail=f"target_name must be one of {sorted(allowed)}")

    out_path = os.path.join(datasets_dir, out_name)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file upload")
    previous = None
    if os.path.exists(out_path):
        try:
            with open(out_path, "rb") as f:
                previous = f.read()
        except OSError:
            previous = None
    try:
        with open(out_path, "wb") as f:
            f.write(content)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Reload registry + replay snapshot
    try:
        core.reload_all()
    except Exception as e:
        # rollback
        try:
            if previous is None:
                os.remove(out_path)
            else:
                with open(out_path, "wb") as f:
                    f.write(previous)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail=f"Upload accepted but dataset reload failed: {e}")

    return sanitize(UploadResponse(ok=True, filename=out_name, dataset_type=dataset_type).model_dump())

