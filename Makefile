.PHONY: help build up down logs seed test clean

help:
	@echo "NCAA Bracket Tracker - Make Commands"
	@echo "===================================="
	@echo "make build       - Build Docker images"
	@echo "make up          - Start all services"
	@echo "make down        - Stop all services"
	@echo "make logs        - View backend logs"
	@echo "make seed        - Seed database with sample data"
	@echo "make test        - Run backend tests"
	@echo "make clean       - Remove all containers and volumes"
	@echo "make frontend    - Install and start frontend"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✓ Services started"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make seed' to populate database"

down:
	docker-compose down

logs:
	docker-compose logs -f backend

seed:
	@echo "Seeding database..."
	docker-compose exec backend python scripts/seed_data.py

test:
	docker-compose exec backend pytest -v

clean:
	docker-compose down -v
	@echo "✓ All containers and volumes removed"

frontend:
	cd frontend && pnpm install && pnpm dev

restart:
	docker-compose restart backend

shell:
	docker-compose exec backend bash
