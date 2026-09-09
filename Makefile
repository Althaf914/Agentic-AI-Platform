.PHONY: setup dev-backend dev-frontend dev test logs

setup: ## 🚀 One-command setup (requires Docker, Python 3.11+, Node 18+)
	cp -n backend/.env.example backend/.env || true
	docker-compose up -d
	@echo "⏳ Waiting for databases to be ready..."
	sleep 3
	cd backend && pip install -r requirements.txt
	cd backend && alembic upgrade head
	cd backend && python -m backend.database.init_db
	cd frontend && npm install
	@echo "✅ Setup complete! Run 'make dev' to start."

dev-backend: ## 🖥️ Start the FastAPI backend (port 8000)
	cd backend && uvicorn backend.main:app --reload --port 8000

dev-frontend: ## 🎨 Start the Vite frontend dev server (port 5173)
	cd frontend && npm run dev

dev: ## 🔥 Start both backend and frontend
	@echo "Starting backend & frontend concurrently..."
	$(MAKE) dev-backend &
	$(MAKE) dev-frontend &
	wait

test: ## 🧪 Run backend test suite
	cd backend && pytest tests/ -v --tb=short

logs: ## 📋 Tail Docker logs
	docker-compose logs -f

shell-backend: ## 🐚 Open a shell in the backend container
	cd backend && python -c "from backend.config import settings; print(settings)"

db-shell: ## 🗄️ Open PostgreSQL shell
	docker exec -it agentforge-postgres psql -U agentforge -d agentforge_db

db-migrate: ## 🔄 Generate a new Alembic migration
	cd backend && alembic revision --autogenerate -m "$(message)"

db-upgrade: ## ⬆️ Apply all pending migrations
	cd backend && alembic upgrade head

clean: ## 🧹 Clean up Docker volumes
	docker-compose down -v
	@echo "✅ All volumes removed. Run 'make setup' to recreate."

help: ## 📖 Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
