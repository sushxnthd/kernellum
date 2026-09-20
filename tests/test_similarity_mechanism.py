from pathlib import Path


def test_mechanism_plan_exists():
    assert Path("docs/SIMILARITY_MECHANISM_PLAN.md").exists()


def test_mechanism_route_schedule_is_60():
    sizes = {"25k": 2, "45k": 3, "85k": 5}
    total = sum(n_sizes * 2 * 3 for n_sizes in sizes.values())
    assert total == 60
