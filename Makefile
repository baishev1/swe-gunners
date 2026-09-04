.DEFAULT_GOAL := help
BACKEND := backend
FRONTEND := frontend

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: install-backend install-frontend ## Install all dependencies

.PHONY: install-backend
install-backend: ## Install backend dependencies
	cd $(BACKEND) && uv sync

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	cd $(FRONTEND) && npm install

.PHONY: dev-backend
dev-backend: ## Run the API with autoreload
	cd $(BACKEND) && uv run uvicorn app.main:app --reload --port 8000

.PHONY: dev-frontend
dev-frontend: ## Run the web client
	cd $(FRONTEND) && npm run dev

.PHONY: lint
lint: ## Lint both projects
	cd $(BACKEND) && uv run ruff check . && uv run mypy app core tests
	cd $(FRONTEND) && npm run lint && npm run typecheck

.PHONY: format
format: ## Format both projects
	cd $(BACKEND) && uv run ruff format . && uv run ruff check --fix .
	cd $(FRONTEND) && npm run format

.PHONY: test
test: ## Run backend tests
	cd $(BACKEND) && uv run pytest

.PHONY: migrate
migrate: ## Apply database migrations
	cd $(BACKEND) && uv run alembic upgrade head

.PHONY: migration
migration: ## Create a migration: make migration m="add events"
	cd $(BACKEND) && uv run alembic revision --autogenerate -m "$(m)"

.PHONY: up
up: ## Start the stack with Docker
	docker compose up --build -d

.PHONY: down
down: ## Stop the stack
	docker compose down
