.PHONY: help build up down restart logs clean test

help:
	@echo "SmartReco - Makefile Commands"
	@echo ""
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - Show logs from all services"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make test       - Run backend tests"
	@echo "  make dev-backend - Run backend in development mode"
	@echo "  make dev-frontend - Run frontend in development mode"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

test:
	cd backend && python -m pytest app/tests/ -v

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev


