.PHONY: setup test proto lint format type-check verify-commit verify build up down logs clean

setup: ## Install deps and pre-commit hooks
	@command -v uv >/dev/null 2>&1 || { echo "Error: uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1;}
	@uv sync --all-groups
	@pre-commit install

sync: ## sync deps
	@uv sync --all-groups

proto: ## Generate the protobuf stubs
	@bash proto-compile.sh

lint: ## Run linting
	@uv run ruff check .

format: ## Run formatting
	@uv run ruff format .

type-check: ## Run Type checking
	@uv run mypy

verify-commit: ## Run pre-commit hooks
	@pre-commit run --all-files

verify: lint format type-check verify-commit

build: ## Build the containers
	@docker compose build

up: ## Run the containers
	@docker compose up --build -d

down: ## tear the containers
	@docker compose down

logs: ## Tail logs from both containers
	@docker compose logs -f

clean: ## Clean everything up
	@docker compose down --rmi all --volumes --remove-orphans
	@docker builder prune -af
	@docker system prune -af --volumes
	@uv cache clean
	@pre-commit clean
	@rm -rf .mypy_cache .ruff_cache __pycache__ **/__pycache__
