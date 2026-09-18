.PHONY: setup test build eda hardware-kit

setup:
	python -m pip install -e '.[test]'

test:
	pytest -q

build:
	python -m kernellum --out artifacts/digits_int8

eda:
	bash scripts/run_eda.sh

hardware-kit:
	test -n "$(BITSTREAM)"
	python scripts/package_krn_hw_001_kit.py build --bitstream "$(BITSTREAM)" --out dist/kernellum-krn-hw-001-kit-v0.1 --zip dist/kernellum-krn-hw-001-kit-v0.1.zip --source-commit "$$(git rev-parse HEAD)"
