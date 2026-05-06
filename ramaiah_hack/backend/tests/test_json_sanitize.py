import math

import numpy as np

from utils.json_sanitize import sanitize


def test_sanitize_nan_inf():
    payload = {"a": float("nan"), "b": float("inf"), "c": np.float64("nan"), "d": 1.0}
    out = sanitize(payload)
    assert out["a"] is None
    assert out["b"] is None
    assert out["c"] is None
    assert out["d"] == 1.0

