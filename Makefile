.PHONY: help install dev lint format typecheck test coverage shell migrate \
        run clean ci

help:           ## Show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed 's/\\$$//' | sed 's/##//'

install:        ## Install production dependencies
	pip install -r requirements.txt

dev:            ## Install dev dependencies (ruff, mypy, pytest, etc.)
	pip install -r requirements-dev.txt

lint:           ## Run ruff linter
	ruff check .

format:         ## Auto-format with ruff
	ruff format .
	ruff check --fix .

typecheck:      ## Run mypy static analysis
	mypy accidents roadsafety

test:           ## Run pytest with coverage (fast)
	pytest --cov=accidents --cov-report=term

coverage:       ## Run tests and generate HTML coverage report
	pytest --cov=accidents --cov-report=html --cov-report=term-missing

shell:          ## Django shell
	python manage.py shell

migrate:        ## Run all migrations
	python manage.py migrate

run:            ## Start dev server
	python manage.py runserver

clean:          ## Remove cache and build artifacts
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov \
	       .coverage coverage.xml staticfiles
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# ===== Docker ==============================================================

docker-build:   ## Build Docker image
	docker compose build

docker-up:      ## Start all Docker services (detached)
	docker compose up -d

docker-down:    ## Stop all Docker services
	docker compose down

docker-logs:    ## Tail Docker logs
	docker compose logs -f

docker-shell:   ## Open a shell in the web container
	docker compose exec web bash

docker-migrate: ## Run Django migrations inside Docker
	docker compose exec web python manage.py migrate

docker-test:    ## Run tests inside Docker
	docker compose exec web python manage.py test --verbosity=2

ci: lint format typecheck test  ## Full CI pipeline (lint → format check → typecheck → test)
