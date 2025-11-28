.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend test test-backend clean build lint format

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend

help: ## Show this help message
	@echo "$(BLUE)BloomFilter Application - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: install-backend install-frontend ## Install all dependencies (backend + frontend)

install-backend: ## Install backend dependencies using uv
	@echo "$(BLUE)Installing backend dependencies with uv...$(NC)"
	cd $(BACKEND_DIR) && uv sync

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && npm install

dev: ## Start both backend and frontend in development mode
	@echo "$(GREEN)Starting backend and frontend...$(NC)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend server with uvicorn
	@echo "$(BLUE)Starting FastAPI backend on http://localhost:8000$(NC)"
	cd $(BACKEND_DIR) && uv run uvicorn main:app --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	@echo "$(BLUE)Starting Vite frontend on http://localhost:5173$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

start: dev ## Alias for 'make dev'

backend: dev-backend ## Alias for 'make dev-backend'

frontend: dev-frontend ## Alias for 'make dev-frontend'

test: test-backend ## Run all tests

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && uv run pytest -v

test-spellcheck: ## Run spellcheck tests specifically
	@echo "$(BLUE)Running spellcheck tests...$(NC)"
	cd $(BACKEND_DIR) && uv run python spellcheck/test_spellcheck.py

test-bloom: ## Run bloom filter tests
	@echo "$(BLUE)Running bloom filter tests...$(NC)"
	cd $(BACKEND_DIR) && uv run pytest tests/test_bloom_filter.py -v

lint-backend: ## Lint backend code
	@echo "$(BLUE)Linting backend...$(NC)"
	cd $(BACKEND_DIR) && uv run ruff check .

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend code...$(NC)"
	cd $(BACKEND_DIR) && uv run ruff format .

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run lint

build-frontend: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run build

clean: ## Clean generated files and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/node_modules 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/.venv 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-pycache: ## Clean only Python cache files
	@echo "$(YELLOW)Cleaning Python cache...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Python cache cleaned!$(NC)"

prod-backend: ## Run backend in production mode
	@echo "$(GREEN)Starting backend in production mode...$(NC)"
	cd $(BACKEND_DIR) && uv run uvicorn main:app --host 0.0.0.0 --port 8000

shell-backend: ## Open a Python shell with backend environment
	@echo "$(BLUE)Opening Python shell...$(NC)"
	cd $(BACKEND_DIR) && uv run python

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	cd $(BACKEND_DIR) && uv sync --upgrade
	cd $(FRONTEND_DIR) && npm update

check: ## Check project health (lint + test)
	@echo "$(BLUE)Running health checks...$(NC)"
	@make test-backend
	@echo "$(GREEN)All checks passed!$(NC)"

info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "  Backend: FastAPI with uv"
	@echo "  Frontend: React with Vite"
	@echo "  Python version: $(shell cd $(BACKEND_DIR) && uv run python --version)"
	@echo "  Node version: $(shell node --version)"
	@echo "  npm version: $(shell npm --version)"
	@echo ""
