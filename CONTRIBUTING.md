# Contributing to Autonomous Blog Generation Agent

Thank you for your interest in contributing to the Autonomous Blog Generation Agent project!

## Development Setup

1. **Prerequisites**:
   - Python 3.11+
   - Astral `uv` package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
   - Node.js 18+ and npm
   - PostgreSQL 16+ running on `localhost:5432` with a database named `blog_db`

2. **Backend Setup**:
   ```bash
   # Sync dependencies
   uv sync

   # Copy environment file
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY or OPENAI_API_KEY and DB credentials

   # Run Alembic migrations
   uv run alembic upgrade head

   # Run FastAPI server
   uv run uvicorn backend.app.main:app --reload --port 8000
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running Tests

Run the backend test suite:
```bash
uv run pytest backend/tests -v
```

## Pull Request Guidelines

1. Ensure all database changes are accompanied by an Alembic migration with a working downgrade function.
2. Maintain existing API response contracts and Pydantic schemas.
3. Keep database writes inside LangGraph nodes centralized through `record_node_step` in `backend/app/agent/persistence.py`.
4. Follow conventional commit messages (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
