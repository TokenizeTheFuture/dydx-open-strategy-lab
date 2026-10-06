import pandas as pd

from open_strategy_lab.data.cache import CsvCache


def test_csv_cache_round_trip(tmp_path):
    cache = CsvCache(tmp_path)
    index = pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC")
    frame = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=index)

    path = cache.save("btc:test", frame)
    loaded = cache.load("btc:test")

    assert path.exists()
    pd.testing.assert_frame_equal(loaded, frame, check_freq=False)
