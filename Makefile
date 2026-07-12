.PHONY: up down build migrate test lint logs

up:
	docker-compose up -d --build
	docker-compose -f docker-compose.dev.yml up -d --build

down:
	docker-compose down

build:
	docker-compose build

migrate:
	docker-compose run --rm backend alembic upgrade head

test:
	pytest -q

lint:
	bandit -r backend || true

logs:
	docker-compose logs -f
