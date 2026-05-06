import pandas as pd

from utils.csv_normalize import normalize_market_csv


def test_normalize_market_handles_bad_timestamps():
    raw = pd.DataFrame({"Date": ["bad", "also-bad"], "Price": [1.0, 2.0], "Volume": [10, 20]})
    try:
        normalize_market_csv(raw, source_name="x.csv")
    except Exception:
        # expected: no timestamps parseable
        assert True
    else:
        assert False, "Expected normalization to fail on fully invalid timestamps"

