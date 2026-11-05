.PHONY: install run test lint format typecheck

install:
	python -m pip install -e ".[dev]"

run:
	python -m uvicorn careercanvas.api:app --host $${CAREERCANVAS_HOST:-127.0.0.1} --port $${CAREERCANVAS_PORT:-8000} --reload

test:
	python -m pytest --cov=careercanvas --cov-report=term-missing --cov-fail-under=85

lint:
	python -m ruff check .

format:
	python -m ruff format .

typecheck:
	python -m mypy

