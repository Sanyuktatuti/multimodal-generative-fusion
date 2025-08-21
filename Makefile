SHELL := /bin/bash

.PHONY: up down logs api worker dev redis

up:
	docker compose -f infra/compose/docker-compose.yaml up -d --build

down:
	docker compose -f infra/compose/docker-compose.yaml down

logs:
	docker compose -f infra/compose/docker-compose.yaml logs -f | cat

api:
	source .venv/bin/activate && export $$(grep -v '^#' .env | xargs) && uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload | cat

worker:
	source .venv/bin/activate && export $$(grep -v '^#' .env | xargs) && celery -A workers.orchestrator.tasks worker --loglevel=INFO | cat

redis:
	docker compose -f infra/compose/docker-compose.yaml up -d redis

# dev: run api and worker locally (requires Redis running)
dev:
	make -j2 api worker
