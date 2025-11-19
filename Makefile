.PHONY: help demo start stop restart logs clean check

# Default target - show help
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

##@ Quick Start

demo: ## 🎬 Run the complete demo (recommended!)
	@./scripts/run-demo.sh

help: ## 📖 Show this help message
	@echo "$(BLUE)🎰 Casino Gaming Loyalty Demo$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(YELLOW)Usage:$(NC) make $(BLUE)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)💡 First time? Just run:$(NC) make demo"
	@echo ""

##@ Basic Commands

start: ## 🚀 Start all services
	@./scripts/run-demo.sh status || docker-compose up -d

stop: ## 🛑 Stop all services
	@./scripts/run-demo.sh stop

restart: ## 🔄 Restart all services
	@./scripts/run-demo.sh restart

clean: ## 🧹 Remove everything (containers + volumes)
	@./scripts/run-demo.sh clean

check: ## 🔍 Check system health
	@./scripts/check-demo.sh

logs: ## 📜 Show all logs
	@docker-compose logs -f

##@ Monitoring

dashboard: ## 🎰 Open Streamlit dashboard
	@open http://localhost:8501 2>/dev/null || xdg-open http://localhost:8501 2>/dev/null || echo "Open http://localhost:8501"

console: ## 📊 Open Redpanda Console
	@open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "Open http://localhost:8080"

status: ## 📈 Show service status
	@docker-compose ps

##@ Data Generation

inject: ## 💉 Start data injection (auto-starts at 5 events/sec)
	@echo "$(BLUE)💉 Starting data injection (5 events/sec)...$(NC)"
	@echo "$(YELLOW)Note: Generator auto-starts on container startup. Only use this if you stopped it manually.$(NC)"
	@curl -s -X POST http://localhost:8000/start | jq '.' || echo "Error: Make sure data-generator service is running"

inject-fast: ## ⚡ Increase rate to 10 events/sec
	@echo "$(BLUE)⚡ Increasing to 10 events/sec...$(NC)"
	@curl -s http://localhost:8000/rate/10 | jq '.' || echo "Error: Make sure data-generator service is running"

inject-slow: ## 🐌 Decrease rate to 2 events/sec
	@echo "$(BLUE)🐌 Decreasing to 2 events/sec...$(NC)"
	@curl -s http://localhost:8000/rate/2 | jq '.' || echo "Error: Make sure data-generator service is running"

inject-rate: ## 📊 Get current event generation rate
	@curl -s http://localhost:8000/rate | jq '.' || echo "Error: Make sure data-generator service is running"

inject-stop: ## 🛑 Stop data injection
	@echo "$(RED)🛑 Stopping data injection...$(NC)"
	@curl -s -X POST http://localhost:8000/stop | jq '.' || echo "Error: Make sure data-generator service is running"

inject-status: ## 📊 Check data injection status
	@curl -s http://localhost:8000/status | jq '.' || echo "Error: Make sure data-generator service is running"
