.PHONY: all clean install test lint format build publish setup-dev test-integration docs

# Default target
all: clean install test lint

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
	# Build Python package
	python -m build
	# Build Rust library
	cargo build --release
	# Copy Rust binary to Python package
	cp target/release/libdolphin.* python/dolphin/

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
	pip install -e ".[dev]"
	# Install Rust toolchain if needed
	command -v rustc >/dev/null 2>&1 || curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
	# Install Solana tools if needed
	command -v solana >/dev/null 2>&1 || sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
	# Install Anchor if needed
	command -v anchor >/dev/null 2>&1 || cargo install --git https://github.com/coral-xyz/anchor avm --locked
	# Install pre-commit hooks
	pre-commit install

# Publish package
publish: clean build
	twine check dist/*
	twine upload dist/*

# Development targets
dev: install
	pip install -e ".[dev]"

watch-test:
	pytest-watch -- tests/unit -v

# Rust-specific targets
build-rust:
	cargo build --release

test-rust:
	cargo test --all-features

# Generate new program
new-program:
	@read -p "Enter program name: " name; \
	read -p "Enter program ID: " id; \
	dolphin init $$name $$id

# Build program
build-program:
	dolphin build

# Deploy program
deploy-program:
	@read -p "Enter network (devnet/mainnet-beta): " network; \
	dolphin deploy --network $$network

# Run program tests
test-program:
	dolphin test

# Validate program
validate: lint test
	dolphin validate

# CI/CD targets
ci: lint test test-integration

# Development utilities
setup-solana:
	sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"
	solana-keygen new --no-bip39-passphrase -o id.json

setup-anchor:
	cargo install --git https://github.com/coral-xyz/anchor avm --locked
	avm install latest
	avm use latest

# Help target
help:
	@echo "Available targets:"
	@echo "  all              : Clean, install, test, and lint"
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
	@echo "  new-program      : Generate new Dolphin program"
	@echo "  build-program    : Build Dolphin program"
	@echo "  deploy-program   : Deploy Dolphin program"
	@echo "  test-program     : Test Dolphin program"
	@echo "  validate         : Validate program"
	@echo "  setup-solana     : Setup Solana tools"
	@echo "  setup-anchor     : Setup Anchor framework"
