.PHONY: dev build publish test lint fmt

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

build:
	python -m build

publish:
	twine upload dist/*

test:
	pytest -q

lint:
	ruff check src tests

fmt:
	ruff check --fix src tests && ruff format src tests
