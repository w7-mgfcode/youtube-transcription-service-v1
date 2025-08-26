# YouTube Transcription Service - Makefile

.PHONY: help build up down logs shell test clean dev prod

# Default target
help:
	@echo "YouTube Transcription Service - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make build     - Build Docker image"
	@echo "  make up        - Start services (development)"
	@echo "  make down      - Stop services"
	@echo "  make logs      - Show logs"
	@echo "  make shell     - Open shell in running container"
	@echo ""
	@echo "Testing:"
	@echo "  make test      - Run tests"
	@echo "  make cli-test  - Test CLI mode interactively"
	@echo "  make api-test  - Test API endpoints"
	@echo ""
	@echo "Production:"
	@echo "  make prod      - Start production services"
	@echo "  make prod-logs - Show production logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean     - Clean up containers and images"
	@echo "  make rebuild   - Clean rebuild"

# Development commands
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec transcribe bash

# Testing
test:
	docker compose run --rm transcribe python -m pytest tests/ -v

cli-test:
	@echo "Testing CLI mode (interactive)..."
	docker compose run --rm transcribe python -m src.main --mode cli --interactive

api-test:
	@echo "Testing API endpoints..."
	@curl -f http://localhost:8000/health || (echo "API not running! Run 'make up' first" && exit 1)
	@echo "✓ Health check passed"
	@echo "✓ API documentation: http://localhost:8000/docs"

# Production
prod:
	docker compose -f docker-compose.prod.yml up -d

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

prod-down:
	docker compose -f docker-compose.prod.yml down

# Maintenance
clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

rebuild: clean build up

# Quick development workflow
dev: build up logs

# Status check
status:
	@echo "=== Container Status ==="
	docker compose ps
	@echo ""
	@echo "=== API Health ==="
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "API not responding"
	@echo ""
	@echo "=== Recent Logs ==="
	docker compose logs --tail=10

# Backup data
backup:
	@echo "Creating backup of data directory..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz data/

# Quick transcription test
quick-test:
	@echo "Running quick transcription test..."
	curl -X POST http://localhost:8000/v1/transcribe \
		-H "Content-Type: application/json" \
		-d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "test_mode": true, "vertex_ai_model": "gemini-2.0-flash"}'