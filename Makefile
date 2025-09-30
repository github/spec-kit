.PHONY: help test test-python test-fish test-all lint format clean install check ci

# Colors
ORANGE := \033[38;5;208m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
CYAN := \033[0;36m
BLUE := \033[0;34m
GRAY := \033[0;90m
NC := \033[0m

# Emoji
TUBE := 🧪
CHECK := ✓
CROSS := ✗
ROCKET := 🚀
GEAR := ⚙️
BROOM := 🧹
BOOK := 📚

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo ""
	@echo "$(ORANGE)╔══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(ORANGE)║                 Spec-Kit Test Suite                      ║$(NC)"
	@echo "$(ORANGE)╚══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(ORANGE)$(TUBE) Testing Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GRAY)Usage: make <target>$(NC)"
	@echo "$(GRAY)Example: make test$(NC)"
	@echo ""

test: test-python test-fish ## Run all tests (Python + Fish)
	@echo ""
	@echo "$(GREEN)$(CHECK) All test suites passed!$(NC)"
	@echo ""

test-python: ## Run Python tests with pytest
	@echo ""
	@echo "$(ORANGE)$(TUBE) Running Python Tests$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@uv run pytest tests/python/ && echo "$(GREEN)$(CHECK) Python tests passed$(NC)" || (echo "$(RED)$(CROSS) Python tests failed$(NC)" && exit 1)
	@echo ""

test-fish: ## Run Fish shell tests with Fishtape
	@echo ""
	@echo "$(ORANGE)$(TUBE) Running Fish Shell Tests$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@if command -v fish >/dev/null 2>&1; then \
		fish -c "fishtape tests/fish/check-prerequisites.test.fish tests/fish/common.test.fish tests/fish/create-new-feature.test.fish tests/fish/setup-plan.test.fish" && echo "$(GREEN)$(CHECK) Fish tests passed$(NC)" || (echo "$(RED)$(CROSS) Fish tests failed$(NC)" && exit 1); \
	else \
		echo "$(YELLOW)⚠ Fish not installed, skipping Fish tests$(NC)"; \
	fi
	@echo ""

test-all: lint test ## Run linting and all tests
	@echo ""
	@echo "$(GREEN)$(ROCKET) Complete test suite passed!$(NC)"
	@echo ""

lint: ## Run Python linting with ruff
	@echo ""
	@echo "$(ORANGE)$(GEAR) Running Code Quality Checks$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(CYAN)Checking code style...$(NC)"
	@uv run ruff check src/ tests/python/ && echo "$(GREEN)$(CHECK) Linting passed$(NC)" || (echo "$(RED)$(CROSS) Linting failed$(NC)" && exit 1)
	@echo "$(CYAN)Checking code formatting...$(NC)"
	@uv run ruff format --check src/ tests/python/ && echo "$(GREEN)$(CHECK) Formatting passed$(NC)" || (echo "$(RED)$(CROSS) Formatting failed$(NC)" && exit 1)
	@echo ""

format: ## Format Python code with ruff
	@echo ""
	@echo "$(ORANGE)$(GEAR) Formatting Python Code$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@uv run ruff format src/ tests/python/
	@echo "$(GREEN)$(CHECK) Code formatted$(NC)"
	@echo ""

install: ## Install development dependencies
	@echo ""
	@echo "$(ORANGE)$(BOOK) Installing Dependencies$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@uv sync --extra dev
	@echo "$(GREEN)$(CHECK) Dependencies installed$(NC)"
	@echo ""

check: ## Check CLI functionality
	@echo ""
	@echo "$(ORANGE)$(TUBE) Testing CLI Installation$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(CYAN)Running: specify --help$(NC)"
	@uv run specify --help > /dev/null && echo "$(GREEN)$(CHECK) CLI help works$(NC)" || (echo "$(RED)$(CROSS) CLI help failed$(NC)" && exit 1)
	@echo "$(CYAN)Running: specify check$(NC)"
	@uv run specify check > /dev/null && echo "$(GREEN)$(CHECK) CLI check works$(NC)" || (echo "$(RED)$(CROSS) CLI check failed$(NC)" && exit 1)
	@echo "$(GREEN)$(CHECK) CLI functional$(NC)"
	@echo ""

clean: ## Clean test artifacts and caches
	@echo ""
	@echo "$(ORANGE)$(BROOM) Cleaning Build Artifacts$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(CYAN)Removing test artifacts...$(NC)"
	@rm -rf htmlcov/ .coverage coverage.xml .pytest_cache/ 2>/dev/null || true
	@echo "$(CYAN)Removing Python caches...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(CYAN)Removing build directories...$(NC)"
	@rm -rf dist/ build/ .eggs/ 2>/dev/null || true
	@echo "$(GREEN)$(CHECK) Cleaned$(NC)"
	@echo ""

ci: ## Run full CI pipeline locally
	@echo ""
	@echo "$(ORANGE)╔══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(ORANGE)║            Running Full CI Pipeline                      ║$(NC)"
	@echo "$(ORANGE)╚══════════════════════════════════════════════════════════╝$(NC)"
	@$(MAKE) clean
	@$(MAKE) install
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) check
	@echo "$(GREEN)╔══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║         $(ROCKET) All CI Checks Passed! $(ROCKET)                   ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""

# Development helpers
.PHONY: test-python-verbose test-fish-verbose coverage watch

test-python-verbose: ## Run Python tests with verbose output
	@echo ""
	@echo "$(ORANGE)$(TUBE) Running Python Tests (Verbose)$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@uv run pytest tests/python/ -vv
	@echo ""

test-fish-verbose: ## Run Fish tests with verbose output
	@echo ""
	@echo "$(ORANGE)$(TUBE) Running Fish Tests (Verbose)$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@fish -c "fishtape tests/fish/check-prerequisites.test.fish tests/fish/common.test.fish tests/fish/create-new-feature.test.fish tests/fish/setup-plan.test.fish" 2>&1
	@echo ""

coverage: ## Generate HTML coverage report
	@echo ""
	@echo "$(ORANGE)$(TUBE) Generating Coverage Report$(NC)"
	@echo "$(GRAY)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@uv run pytest tests/python/ --cov=src/specify_cli --cov-report=html --cov-report=term
	@echo ""
	@echo "$(GREEN)$(CHECK) Coverage report generated: $(CYAN)htmlcov/index.html$(NC)"
	@echo ""

watch: ## Run tests on file changes (requires entr)
	@echo ""
	@echo "$(ORANGE)$(TUBE) Watching for changes...$(NC)"
	@echo "$(GRAY)Press Ctrl+C to stop$(NC)"
	@echo ""
	@find src/ tests/ -name "*.py" | entr -c make test-python
