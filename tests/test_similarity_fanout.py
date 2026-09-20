from pathlib import Path

from scripts.similarity_fanout_route import FANOUTS


def test_fanout_plan_exists():
    assert Path("docs/SIMILARITY_FANOUT_PLAN.md").exists()


def test_fanout_values_divide_array_size():
    for n, fanouts in FANOUTS.items():
        assert len(fanouts) == 4
        assert all(n % f == 0 for f in fanouts)


def test_fanout_route_schedule_is_144():
    total = sum(len(v) * len(v) * 3 for v in FANOUTS.values())
    assert total == 144
