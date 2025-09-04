.PHONY: help install install-dev test test-cov lint format type-check clean build docs serve-docs

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev,docs]"
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=musicbrainz_mcp --cov-report=html --cov-report=term

lint:  ## Run linting
	ruff check src tests
	black --check src tests

format:  ## Format code
	black src tests
	ruff check --fix src tests

type-check:  ## Run type checking
	mypy src

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python -m build

docs:  ## Build documentation
	mkdocs build

serve-docs:  ## Serve documentation locally
	mkdocs serve

run:  ## Run the MCP server
	python -m musicbrainz_mcp.server

dev-setup: install-dev  ## Complete development setup
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."
