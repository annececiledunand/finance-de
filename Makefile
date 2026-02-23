.ONESHELL:
.PHONY: help install init linter test coverage remove-app run-app

# help target that shows the target documentation. Need to start with \#\#
# Source: https://github.com/cargo-bins/cargo-quickinstall/blob/283a09f4ca33b4d4c700c1e8350a93aff8957132/Makefile#L71
help:
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# targets

## Code targets

install:  ## Create and activate a virtualenv at .venv, install all python libs.
	@echo "Creates a new virtualenv at .venv and sync all libs"
	uv venv --clear
	uv sync --all-extras --no-install-project

init:  ## Install uv, your complete virtualenv and the pre-commit. Run once.
	@echo "Installs uv"
	command -v uv >/dev/null 2>&1 && echo "uv is already installed" || curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh
	uv python install
	$(MAKE) install
	@echo "Installs pre-commit"
	uv run pre-commit install

linter:  ## Check style with ruff and mypy.
	@echo "Runs all formatting tools on root"
	uv run ruff format .
	uv run ruff check . --fix
	uv run mypy .

test: ## Run tests.
	uv run python -m pytest

coverage: ## Check code coverage.
	@echo "Coverage report generating in htmlcov/ and coverage.xml"
	uv run python -m pytest --cov-report=html --cov-report=xml --no-cov-on-fail

## app targets (fastapi & sql)
run-app:  ## Dev entrypoint: Build and start FastAPI app with sync on modifications
	@echo "Build app (with cache)..."
	docker compose -f deploy/compose.yml build
	@echo "Up app container (with watching api folder)..."
	docker compose -f deploy/compose.yml up --watch

remove-app:  ## Stop and remove containers, networks, AND volumes created by ‘up’. (!do not remove orphans since it will refer to other services containers)
	@echo "Stopping and removing app containers and volumes..."
	docker compose -f deploy/compose.yml down --volumes

init-db:
	@echo "Run init script of db in a transaction. !Will drop and re-create if already exists!"
	@export $$(cat ./deploy/.env | xargs) && psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@localhost:$${POSTGRES_PORT}/$${POSTGRES_DB}" -f src/database/sql/create_db.sql
