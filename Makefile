install:
	poetry install --with dev

lint:
	poetry run ruff check lcovparser.py
	poetry run mypy lcovparser.py

test:
	poetry run pytest

check: lint test

clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache

.PHONY: check install lint test
