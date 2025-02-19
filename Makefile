.PHONY: all clean install test lint format build publish setup-dev test-integration docs verify

# Default target
all: verify build test

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .tox
	rm -rf target/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete

# Install package in development mode
install:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/unit -v --cov=dolphin --cov-report=term-missing

# Run integration tests
test-integration:
	pytest tests/integration -v --cov=dolphin --cov-report=term-missing

# Run linters
lint:
	flake8 python/dolphin
	mypy python/dolphin
	black --check python/dolphin
	isort --check-only python/dolphin
	cargo clippy --all-targets --all-features -- -D warnings

# Format code
format:
	black python/dolphin
	isort python/dolphin
	cargo fmt --all

# Build package
build: clean
	# Build Rust library
	maturin build --release
	# Build Python package
	python -m build

# Build documentation
docs:
	mkdocs build

# Serve documentation locally
serve-docs:
	mkdocs serve

# Initialize development environment
init-dev: clean
	# Install Python dependencies
	python -m pip install --upgrade pip
	pip install -e ".[dev,docs]"
	# Install Rust toolchain if needed
	command -v rustc >/dev/null 2>&1 || curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
	# Install Solana tools if needed
	command -v solana >/dev/null 2>&1 || sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
	# Install Anchor if needed
	command -v anchor >/dev/null 2>&1 || cargo install --git https://github.com/coral-xyz/anchor avm --locked
	avm install latest
	avm use latest
	# Install pre-commit hooks
	pre-commit install

# Publish package
publish: clean verify build
	twine check dist/*
	twine upload dist/*

# Development targets
dev: install
	pip install -e ".[dev]"

watch-test:
	pytest-watch -- tests/unit -v

# Rust-specific targets
build-rust:
	maturin build --release

test-rust:
	cargo test --all-features

# Verify project setup
verify: lint test
	python -m build
	twine check dist/*

# Development utilities
setup-solana:
	sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
	solana-keygen new --no-bip39-passphrase -o id.json

setup-anchor:
	cargo install --git https://github.com/coral-xyz/anchor avm --locked
	avm install latest
	avm use latest

# Docker targets
docker-build:
	docker build -t dolphin-dev .

docker-test:
	docker run --rm dolphin-dev make test

# Help target
help:
	@echo "Available targets:"
	@echo "  all              : Clean, verify, build and test"
	@echo "  clean            : Remove build artifacts"
	@echo "  install          : Install package in development mode"
	@echo "  test             : Run unit tests"
	@echo "  test-integration : Run integration tests"
	@echo "  lint             : Run linters"
	@echo "  format           : Format code"
	@echo "  build            : Build package"
	@echo "  docs             : Build documentation"
	@echo "  serve-docs       : Serve documentation locally"
	@echo "  init-dev         : Initialize development environment"
	@echo "  publish          : Publish package"
	@echo "  verify           : Verify project setup"
	@echo "  setup-solana     : Setup Solana tools"
	@echo "  setup-anchor     : Setup Anchor framework"
	@echo "  docker-build     : Build Docker development image"
	@echo "  docker-test      : Run tests in Docker"

# CI/CD targets
ci: verify test test-integration

# Development workflow targets
dev-setup: init-dev setup-solana setup-anchor

# Build and test in one command
build-test: build test test-integration

# Quick development cycle
quick-dev: format lint test
