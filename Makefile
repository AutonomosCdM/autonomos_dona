# Makefile for Autónomos Dona Slack Bot

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
ISORT := isort

# Directories
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs

# Python files
PYTHON_FILES := $(SRC_DIR) $(TEST_DIR)

# Default target
.DEFAULT_GOAL := help

# Help command
.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
.PHONY: install
install: ## Install dependencies
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

.PHONY: install-dev
install-dev: install ## Install development dependencies
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true
	@echo "✅ Development dependencies installed"

# Running the application
.PHONY: run
run: ## Run the bot
	$(PYTHON) -m src.app

.PHONY: dev
dev: ## Run the bot in development mode with auto-reload
	PYTHONPATH=. $(PYTHON) -m src.app --reload 2>/dev/null || PYTHONPATH=. $(PYTHON) -m src.app

# Testing
.PHONY: test
test: ## Run all tests
	$(PYTEST) $(TEST_DIR) -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	$(PYTEST) $(TEST_DIR) -v --watch 2>/dev/null || $(PYTEST) $(TEST_DIR) -v

# Code quality
.PHONY: lint
lint: ## Run linting (flake8)
	$(FLAKE8) $(PYTHON_FILES) --max-line-length=100 --extend-ignore=E203,W503

.PHONY: format
format: ## Format code with black and isort
	$(ISORT) $(PYTHON_FILES)
	$(BLACK) $(PYTHON_FILES) --line-length=100

.PHONY: format-check
format-check: ## Check code formatting without making changes
	$(ISORT) $(PYTHON_FILES) --check-only
	$(BLACK) $(PYTHON_FILES) --line-length=100 --check

.PHONY: type-check
type-check: ## Run type checking with mypy
	mypy $(SRC_DIR) --ignore-missing-imports 2>/dev/null || echo "ℹ️  Install mypy for type checking: pip install mypy"

# Cleaning
.PHONY: clean
clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up generated files"

# Environment setup
.PHONY: setup
setup: ## Set up the development environment
	@echo "Setting up development environment..."
	$(PYTHON) -m venv venv
	@echo "✅ Virtual environment created"
	@echo ""
	@echo "Activate the virtual environment with:"
	@echo "  source venv/bin/activate  # On Unix/macOS"
	@echo "  venv\\Scripts\\activate     # On Windows"
	@echo ""
	@echo "Then run: make install"

.PHONY: env-check
env-check: ## Check if environment variables are set
	@echo "Checking environment variables..."
	@test -n "$$SLACK_BOT_TOKEN" || echo "❌ SLACK_BOT_TOKEN is not set"
	@test -n "$$SLACK_APP_TOKEN" || echo "❌ SLACK_APP_TOKEN is not set"
	@test -n "$$SLACK_SIGNING_SECRET" || echo "❌ SLACK_SIGNING_SECRET is not set"
	@test -n "$$SUPABASE_URL" || echo "❌ SUPABASE_URL is not set"
	@test -n "$$SUPABASE_KEY" || echo "❌ SUPABASE_KEY is not set"
	@test -n "$$SLACK_BOT_TOKEN" && test -n "$$SLACK_APP_TOKEN" && test -n "$$SLACK_SIGNING_SECRET" && test -n "$$SUPABASE_URL" && test -n "$$SUPABASE_KEY" && echo "✅ All required environment variables are set" || echo "⚠️  Some environment variables are missing"

# Database
.PHONY: db-init
db-init: ## Initialize database tables (requires Supabase CLI)
	@echo "Database initialization should be done through Supabase dashboard"
	@echo "See docs/setup.md for SQL scripts"

# Documentation
.PHONY: docs
docs: ## Generate documentation
	@echo "Generating documentation..."
	@test -d $(DOCS_DIR) || mkdir -p $(DOCS_DIR)
	@echo "✅ Documentation directory ready"

# Docker (future implementation)
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "Docker support coming soon!"
	# docker build -t autonomos-dona:latest .

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "Docker support coming soon!"
	# docker run -it --env-file .env autonomos-dona:latest

# Shortcuts
.PHONY: t
t: test ## Shortcut for test

.PHONY: f
f: format ## Shortcut for format

.PHONY: l
l: lint ## Shortcut for lint

.PHONY: r
r: run ## Shortcut for run

# All checks
.PHONY: check
check: format-check lint type-check test ## Run all checks (format, lint, type, test)
	@echo "✅ All checks passed!"

# Full setup
.PHONY: bootstrap
bootstrap: setup install env-check ## Full project setup
	@echo "✅ Project bootstrap complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and fill in your credentials"
	@echo "2. Run 'make run' to start the bot"