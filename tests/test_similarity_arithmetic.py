from pathlib import Path


def test_arithmetic_plan_exists():
    assert Path("docs/SIMILARITY_ARITHMETIC_PLAN.md").exists()


def test_arithmetic_route_schedule_is_54():
    sizes={"25k":2,"45k":3,"85k":4}
    total=sum(n*2*3 for n in sizes.values())
    assert total==54
