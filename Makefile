.PHONY: help install start stop restart logs status setup-device list-devices backup ssl-renew clean

# Default docker-compose file
COMPOSE_FILE := docker-compose.yml

help:
	@echo "Obsidian LiveSync Server - Management Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Initial deployment (runs deploy.sh)"
	@echo ""
	@echo "Service Management:"
	@echo "  make start            - Start all services"
	@echo "  make stop             - Stop all services"
	@echo "  make restart          - Restart all services"
	@echo "  make logs             - View logs (follow mode)"
	@echo "  make status           - Show service status"
	@echo ""
	@echo "Device Management:"
	@echo "  make setup-device DEVICE=<name>    - Generate setup URI for device"
	@echo "  make list-devices                  - List all registered devices"
	@echo ""
	@echo "Maintenance:"
	@echo "  make backup           - Backup CouchDB database"
	@echo "  make ssl-renew        - Renew SSL certificates"
	@echo "  make clean            - Stop services and remove volumes (⚠️  DESTRUCTIVE)"
	@echo ""
	@echo "Examples:"
	@echo "  make setup-device DEVICE=\"MyPhone\""
	@echo "  make logs"

install:
	@echo "🚀 Running deployment script..."
	@./deploy.sh

start:
	@echo "▶️  Starting services..."
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Services started"

stop:
	@echo "⏹️  Stopping services..."
	@docker-compose -f $(COMPOSE_FILE) down
	@echo "✅ Services stopped"

restart:
	@echo "🔄 Restarting services..."
	@docker-compose -f $(COMPOSE_FILE) restart
	@echo "✅ Services restarted"

logs:
	@docker-compose -f $(COMPOSE_FILE) logs -f

status:
	@docker-compose -f $(COMPOSE_FILE) ps

setup-device:
ifndef DEVICE
	@echo "❌ Error: DEVICE name is required"
	@echo "   Usage: make setup-device DEVICE=\"MyPhone\""
	@exit 1
endif
	@echo "📱 Setting up device: $(DEVICE)"
	@docker exec obsidian-auth python3 setup_uri.py "$(DEVICE)"

list-devices:
	@echo "📋 Registered devices:"
	@docker exec obsidian-auth python3 cli.py list

backup:
	@echo "💾 Creating backup..."
	@docker exec obsidian-couchdb /app/scripts/backup.sh
	@echo "✅ Backup complete"

ssl-renew:
	@echo "🔒 Renewing SSL certificates..."
	@docker exec obsidian-nginx certbot renew
	@docker exec obsidian-nginx nginx -s reload
	@echo "✅ SSL certificates renewed"

clean:
	@echo "⚠️  WARNING: This will stop all services and DELETE ALL DATA!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "🗑️  Removing services and volumes..."
	@docker-compose -f $(COMPOSE_FILE) down -v
	@echo "✅ Cleanup complete"
