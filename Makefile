.PHONY: up down build logs test clean

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	cd backend && pytest -v

clean:
	docker compose down -v
