.PHONY: help lint format format-check test coverage pre-commit all

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z0-9][a-zA-Z0-9_-]+:.*##/ {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

lint: ## Run Ruff lint
	uv run ruff check

format: ## Run Ruff formatter
	uv run ruff format

format-check: ## Check formatting with Ruff
	uv run ruff format --check

test: ## Run pytest
	uv run pytest

coverage: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=term-missing

pre-commit: ## Run all pre-commit hooks on all files
	pre-commit run --all-files

all: lint format-check test coverage ## Run lint, format-check, tests, and coverage
