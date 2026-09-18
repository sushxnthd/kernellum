import csv
import json
from pathlib import Path

import numpy as np

from scripts.analyze_measurements import integrate_power_window, read_windows


def test_read_windows_and_power_integration(tmp_path: Path):
    latency = tmp_path / "latency.csv"
    latency.write_text("start_s,done_s\n0.1,0.10001\n0.2,0.20002\n")
    windows = read_windows(latency)
    assert windows == [(0.1, 0.10001), (0.2, 0.20002)]

    times = np.array([0.0, 0.1, 0.2, 0.3])
    power = np.array([1.0, 2.0, 2.0, 1.0])
    energy = integrate_power_window(times, power, 0.1, 0.2, None)
    assert energy > 0
