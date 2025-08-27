# YouTube Transcription Service - Makefile

.PHONY: help build up down logs shell test test-unit test-integration test-api test-performance test-coverage test-all clean dev prod

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
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-api       - Run API endpoint tests"
	@echo "  make test-performance - Run performance benchmarks"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make test-all       - Run comprehensive test suite"
	@echo "  make cli-test       - Test CLI mode interactively"
	@echo "  make api-test       - Test live API endpoints"
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

# Testing Commands

# Basic test command (all tests)
test:
	@echo "Running all tests..."
	docker compose run --rm transcribe python -m pytest tests/ -v

# Unit tests for specific modules
test-unit:
	@echo "Running unit tests..."
	docker compose run --rm transcribe python -m pytest tests/test_translator.py tests/test_synthesizer.py tests/test_video_muxer.py tests/test_dubbing_service.py tests/test_chunking.py tests/test_validators.py tests/test_config.py -v

# Integration tests
test-integration:
	@echo "Running integration tests..."
	docker compose run --rm transcribe python -m pytest tests/test_integration.py -v

# API endpoint tests  
test-api:
	@echo "Running API tests..."
	docker compose run --rm transcribe python -m pytest tests/test_api_dubbing.py -v

# Performance benchmarks
test-performance:
	@echo "Running performance tests..."
	docker compose run --rm transcribe python -m pytest tests/test_performance.py -v -s

# Test coverage report
test-coverage:
	@echo "Running tests with coverage report..."
	docker compose run --rm transcribe python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v
	@echo "Coverage report generated in htmlcov/index.html"

# Comprehensive test suite
test-all: test-unit test-integration test-api
	@echo "All test suites completed successfully!"

# Interactive CLI testing
cli-test:
	@echo "Testing CLI mode (interactive)..."
	docker compose run --rm transcribe python -m src.main --mode cli --interactive

# Live API endpoint testing
api-test:
	@echo "Testing live API endpoints..."
	@curl -f http://localhost:8000/health || (echo "API not running! Run 'make up' first" && exit 1)
	@echo "✓ Health check passed"
	@echo "✓ Testing dubbing endpoints..."
	@curl -s -X GET http://localhost:8000/v1/voices || echo "Dubbing endpoints test failed"
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

# Quick testing commands
quick-test:
	@echo "Running quick transcription test..."
	curl -X POST http://localhost:8000/v1/transcribe \
		-H "Content-Type: application/json" \
		-d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "test_mode": true, "vertex_ai_model": "gemini-2.0-flash"}'

# Quick dubbing test
quick-dub-test:
	@echo "Running quick dubbing test..."
	curl -X POST http://localhost:8000/v1/dub \
		-H "Content-Type: application/json" \
		-d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "test_mode": true, "enable_translation": true, "target_language": "en-US", "enable_synthesis": false, "enable_video_muxing": false}'

# Test cost estimation
test-cost-estimate:
	@echo "Testing cost estimation..."
	curl -X GET "http://localhost:8000/v1/cost-estimate?transcript_length=1000&target_language=en-US&enable_synthesis=true"

# Test available voices
test-voices:
	@echo "Testing available voices..."
	curl -X GET http://localhost:8000/v1/voices

# Docker management
docker-stats:
	@echo "=== Docker Resource Usage ==="
	docker compose exec transcribe df -h /app
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Update dependencies
update-deps:
	@echo "Updating yt-dlp and other dependencies..."
	docker compose run --rm transcribe pip install --upgrade yt-dlp elevenlabs
	docker compose restart

# Environment validation
validate-env:
	@echo "Validating environment configuration..."
	docker compose run --rm transcribe python -c "from src.config import settings; print('✓ Configuration loaded successfully'); print(f'✓ GCS Bucket: {settings.gcs_bucket_name}'); print(f'✓ Vertex Project: {settings.vertex_project_id}'); print(f'✓ Dubbing Enabled: {settings.enable_translation}')"

# Monitor logs in real-time
monitor:
	@echo "Monitoring service logs and health..."
	docker compose logs -f --tail=50

# Full development setup
setup-dev: build
	@echo "Setting up development environment..."
	@echo "Creating data and temp directories..."
	mkdir -p data temp temp/videos credentials
	@echo "Starting services..."
	make up
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Testing API health..."
	make api-test
	@echo "✓ Development environment ready!"
	@echo "  • API: http://localhost:8000"
	@echo "  • Docs: http://localhost:8000/docs"
	@echo "  • Logs: make logs"
	@echo "  • Shell: make shell"