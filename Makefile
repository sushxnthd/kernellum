.PHONY: setup test build eda

setup:
	python -m pip install -e '.[test]'

test:
	pytest -q

build:
	python -m kernellum --out artifacts/digits_int8

eda:
	bash scripts/run_eda.sh
