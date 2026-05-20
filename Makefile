.PHONY: up down build test seed migrate eval lint clean health worker

IMAGE_NAME ?= docint-workbench
TAG ?= local

up:
	docker compose up --build -d

down:
	docker compose down -v

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

test:
	pytest -q

seed:
	python examples/seed_data.py

migrate:
	python scripts/migrate_database.py

eval:
	@if [ -x .venv/bin/python ]; then .venv/bin/python evals/run_evals.py; else python3 evals/run_evals.py; fi

worker:
	python scripts/run_queue_worker.py

lint:
	ruff check . --ignore=F401 2>/dev/null || echo "Lint warnings noted"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null

health:
	curl -s http://localhost:8005/health | python -m json.tool
