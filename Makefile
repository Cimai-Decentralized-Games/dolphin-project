.PHONY: all clean install test lint format build publish

all: clean install test lint

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .tox
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=dolphin --cov-report=term-missing

test-integration:
	pytest tests/integration -v --cov=dolphin --cov-report=term-missing

lint:
	flake8 python/dolphin
	mypy python/dolphin
	black --check python/dolphin
	isort --check-only python/dolphin

format:
	black python/dolphin
	isort python/dolphin

build:
	python -m build

build-rust:
	cargo build --release

publish:
	twine upload dist/*

dev:
	pip install -e ".[dev]"

watch-test:
	pytest-watch -- tests/ -v

docs:
	mkdocs build

serve-docs:
	mkdocs serve

init-dev: clean
	python -m pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install

validate: lint test