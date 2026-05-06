from __future__ import annotations

from typing import Any

import numpy as np


def sanitize(obj: Any) -> Any:
    """
    Make objects safe for JSON serialization:
    - convert NaN/Inf (python float or numpy scalar) -> None
    - convert numpy scalars -> python scalars
    - sanitize nested dict/list structures
    """
    if obj is None:
        return None

    # numpy scalars
    if isinstance(obj, (np.floating, np.integer)):
        v = obj.item()
        return sanitize(v)

    # python numbers
    if isinstance(obj, float):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, int):
        return int(obj)

    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]

    return obj

