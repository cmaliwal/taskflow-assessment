.PHONY: help install lint fmt typecheck test coverage migrate seed check

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies and pre-commit hooks
	pip install -r requirements-dev.txt && pre-commit install

lint: ## Run ruff linter
	ruff check .

fmt: ## Run ruff formatter
	ruff format .

typecheck: ## Run mypy type checker
	mypy common projects taskflow

test: ## Run the test suite
	pytest

coverage: ## Run tests with coverage report (fails below 80%)
	pytest --cov=common --cov=projects --cov=taskflow --cov-report=term-missing --cov-fail-under=80

migrate: ## Apply all pending migrations
	python manage.py migrate

seed: ## Seed the database with realistic data
	python manage.py seed_data --projects 5 --tasks-per-project 8

check: lint typecheck test ## Run all checks (lint + typecheck + test)
