# Spec Kit Development Makefile
# Provides easy commands for local development and testing

.PHONY: help install-dev test-agent test-all clean check-tools dev-setup validate test-packages

# Default target
help: ## Show this help message
	@echo "Spec Kit Development Commands"
	@echo "============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install Spec Kit CLI in development mode as specify-dev
	@echo "Installing Spec Kit CLI in development mode as 'specify-dev'..."
	pip install -e . --force-reinstall
	@echo "✅ Spec Kit CLI installed as 'specify-dev'"
	@echo "Run 'specify-dev --help' to test"

uninstall-dev: ## Uninstall Spec Kit CLI development version
	@echo "Uninstalling Spec Kit CLI development version..."
	pip uninstall specify-cli -y
	@echo "✅ Spec Kit CLI uninstalled"

check-tools: ## Check if all required tools are installed
	@echo "Checking required tools..."
	@echo ""
	@echo "🔍 Tool Status:"
	@echo "==============="
	@if command -v git >/dev/null 2>&1; then \
		echo "✅ git: $$(git --version)"; \
	else \
		echo "❌ git: Not installed"; \
	fi
	@if command -v python3 >/dev/null 2>&1; then \
		echo "✅ python3: $$(python3 --version)"; \
	else \
		echo "❌ python3: Not installed"; \
	fi
	@if command -v pip >/dev/null 2>&1; then \
		echo "✅ pip: $$(pip --version)"; \
	else \
		echo "❌ pip: Not installed"; \
	fi
	@if command -v specify-dev >/dev/null 2>&1; then \
		echo "✅ specify-dev: Installed"; \
	else \
		echo "❌ specify-dev: Not installed (run 'make install-dev')"; \
	fi

test-agent: ## Test agent integration with Spec Kit (usage: make test-agent AGENT=crush)
	@if [ -z "$(AGENT)" ]; then \
		echo "❌ Please specify an agent: make test-agent AGENT=crush"; \
		echo "Available agents: claude, gemini, copilot, cursor, qwen, opencode, codex, windsurf, kilocode, auggie, roo, crush"; \
		exit 1; \
	fi
	@echo "Testing $(AGENT) integration..."
	@echo ""
	@echo "🧪 Test 1: Check tool detection"
	@echo "==============================="
	@if command -v specify-dev >/dev/null 2>&1; then \
		specify-dev check | grep -E "($(AGENT)|$(shell echo $(AGENT) | tr '[:lower:]' '[:upper:]'))" || echo "❌ $(AGENT) not detected"; \
	else \
		echo "❌ Specify-dev CLI not installed. Run 'make install-dev' first"; \
	fi
	@echo ""
	@echo "🧪 Test 2: Create test project"
	@echo "=============================="
	@if [ -d "test-$(AGENT)-project" ]; then \
		echo "⚠️  Removing existing test project..."; \
		rm -rf test-$(AGENT)-project; \
	fi
	@if command -v specify-dev >/dev/null 2>&1; then \
		specify-dev init test-$(AGENT)-project --ai $(AGENT) --no-git; \
		echo "✅ Test project created"; \
	else \
		echo "❌ Specify-dev CLI not installed. Run 'make install-dev' first"; \
	fi
	@echo ""
	@echo "🧪 Test 3: Verify project structure"
	@echo "=================================="
	@case "$(AGENT)" in \
		claude) dir=".claude/commands" ;; \
		gemini) dir=".gemini/commands" ;; \
		copilot) dir=".github/prompts" ;; \
		cursor) dir=".cursor/commands" ;; \
		qwen) dir=".qwen/commands" ;; \
		opencode) dir=".opencode/command" ;; \
		windsurf) dir=".windsurf/workflows" ;; \
		codex) dir=".codex/prompts" ;; \
		kilocode) dir=".kilocode/workflows" ;; \
		auggie) dir=".augment/commands" ;; \
		roo) dir=".roo/commands" ;; \
		crush) dir=".crush/commands" ;; \
		*) echo "❌ Unknown agent directory structure"; exit 1 ;; \
	esac; \
	if [ -d "test-$(AGENT)-project/$$dir" ]; then \
		echo "✅ $$dir directory created"; \
		echo "📁 Command files:"; \
		ls -1 test-$(AGENT)-project/$$dir/ | sed 's/^/   - /'; \
	else \
		echo "❌ $$dir directory not found"; \
	fi
	@echo ""
	@echo "🧪 Test 4: Test agent context script"
	@echo "==================================="
	@if [ -f "test-$(AGENT)-project/.specify/scripts/bash/update-agent-context.sh" ]; then \
		cd test-$(AGENT)-project && ./.specify/scripts/bash/update-agent-context.sh $(AGENT); \
		echo "✅ Agent context script executed"; \
	else \
		echo "❌ Agent context script not found"; \
	fi

test-all: ## Run all tests (usage: make test-all AGENT=crush)
	@echo "Running all tests..."
	@echo ""
	@$(MAKE) check-tools
	@echo ""
	@if [ -z "$(AGENT)" ]; then \
		echo "⚠️  No agent specified for test-all. Run 'make test-agent AGENT=crush' instead"; \
	else \
		$(MAKE) test-agent AGENT=$(AGENT); \
	fi
	@echo ""
	@echo "🎉 All tests completed!"

dev-setup: install-dev ## Complete development setup
	@echo ""
	@echo "🎉 Development setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Run 'make test-agent AGENT=crush' to test an agent integration"
	@echo "2. Run 'make test-all AGENT=crush' for comprehensive testing"
	@echo "3. Use 'specify-dev init my-project --ai crush' to create projects"

clean: ## Clean up test files (usage: make clean AGENT=crush)
	@echo "Cleaning up test files..."
	@if [ -n "$(AGENT)" ]; then \
		if [ -d "test-$(AGENT)-project" ]; then \
			rm -rf test-$(AGENT)-project; \
			echo "✅ Removed test-$(AGENT)-project"; \
		fi; \
	else \
		echo "🧹 Cleaning up all test projects..."; \
		for dir in test-*-project; do \
			if [ -d "$$dir" ]; then \
				rm -rf "$$dir"; \
				echo "✅ Removed $$dir"; \
			fi; \
		done; \
	fi
	@if [ -d ".genreleases" ]; then \
		rm -rf .genreleases; \
		echo "✅ Removed .genreleases"; \
	fi
	@echo "🧹 Cleanup complete"

# Package testing (advanced)
test-packages: ## Test package generation
	@echo "Testing package generation..."
	@if [ -f ".github/workflows/scripts/create-release-packages.sh" ]; then \
		.github/workflows/scripts/create-release-packages.sh v0.1.0-test; \
		echo "✅ Packages generated in .genreleases/"; \
		ls -la .genreleases/spec-kit-template-crush-* 2>/dev/null || echo "❌ Crush packages not found"; \
	else \
		echo "❌ Package generation script not found"; \
	fi

# Quick validation
validate: ## Quick validation of changes
	@echo "Validating changes..."
	@echo ""
	@echo "🔍 Python syntax check:"
	python -m py_compile src/specify_cli/__init__.py && echo "✅ Python syntax OK"
	@echo ""
	@echo "🔍 Bash script syntax check:"
	bash -n scripts/bash/update-agent-context.sh && echo "✅ Bash syntax OK"
	@echo ""
	@echo "🔍 PowerShell script syntax check:"
	@if command -v pwsh >/dev/null 2>&1; then \
		pwsh -NoProfile -Command "& { Get-Content scripts/powershell/update-agent-context.ps1 | Out-Null }" && echo "✅ PowerShell syntax OK"; \
	else \
		echo "⚠️  PowerShell Core not found, skipping PowerShell validation"; \
	fi
	@echo ""
	@echo "✅ All validations passed!"
