.PHONY: build up down logs restart shell clean

# Production commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f telegram-bot

restart:
	docker-compose restart telegram-bot

shell:
	docker-compose exec telegram-bot /bin/bash

clean:
	docker-compose down -v
	docker system prune -f

# Development commands
dev-build:
	docker-compose -f docker-compose.dev.yml build

dev-up:
	docker-compose -f docker-compose.dev.yml up

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

dev-shell:
	docker-compose -f docker-compose.dev.yml exec telegram-bot /bin/bash

# Utility commands
ps:
	docker-compose ps

stats:
	docker stats telegram-applicant-bot

inspect:
	docker-compose exec telegram-bot python -c "from config.settings import *; print('Bot configured successfully!')"
