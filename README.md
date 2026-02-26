# Companis

*com + panis* — Latin for "with bread." The root of the word *companion*: one who shares bread with you.

Companis is a personalized eating lifestyle app. It builds a comprehensive profile of who you are as an eater — your health conditions, cooking attitudes, flavor preferences, budget, and more — and uses that profile to recommend recipes tailored to how you actually want to eat.

This is not a "healthy eating" app. It's an app that understands how you eat and helps you do it better, whether that means heart-healthy meals, budget-friendly quick dinners, or adventurous weekend cooking projects.

## Features

- Personalized eating profile (health conditions, cooking style, flavor preferences)
- AI-powered recipe generation respecting your dietary constraints and preferences
- Pantry inventory management with barcode scanning
- Household support with family dietary needs
- Shopping list generation
- Multiple AI provider support (Ollama, Anthropic, OpenAI)

## Monorepo Structure

- `backend/` - Python 3.12 FastAPI API server
- `frontend/` - Vue 3 + TypeScript SPA with Capacitor for mobile
- `docker-compose.yml` - Local development with Docker

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env  # edit as needed
python -m app
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up
```

## Ports

| Service  | Port  |
|----------|-------|
| Backend  | 6000  |
| Frontend | 6001  |
| Ollama   | 11434 |

The frontend dev server proxies `/api` requests to the backend at `localhost:6000`.

## Configuration

Hierarchical config with priority (highest first):
1. CLI args (`python -m app --port=8000 --ai-provider=anthropic`)
2. Secrets files (`/run/secrets`, `/etc/secrets`)
3. Environment variables
4. `.env` file
5. Defaults

All settings are defined in `backend/app/config.py`. Any setting can be set from any source.

## AI Providers

Set `AI_PROVIDER` (env) or `--ai-provider` (CLI):

| Provider       | Value          | Requires                     |
|----------------|----------------|------------------------------|
| Ollama (local) | `ollama`       | Ollama running on port 11434 |
| Anthropic      | `anthropic`    | `ANTHROPIC_API_KEY`          |
| OpenAI         | `openai`       | `OPENAI_API_KEY`             |
| Claude Code    | `claude_local` | Claude Code CLI installed    |

Default: `ollama` with `llama3.2` model.

## Database

SQLite with async SQLAlchemy (`aiosqlite`). File: `backend/companis.db`. Migrations via Alembic.

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Testing

```bash
# Backend
cd backend
pytest                          # all tests
pytest tests/unit/              # unit only
pytest --cov=app                # with coverage

# Frontend
cd frontend
npm test                        # vitest unit tests
npm run test:coverage           # with coverage
npm run test:e2e                # playwright E2E
```

## Linting

```bash
# Backend
cd backend
ruff check .                    # lint
ruff format .                   # format
pyright                         # type check
bandit -r app/                  # security scan

# Frontend
cd frontend
npm run lint                    # eslint --fix
npm run lint:check              # eslint (no fix)
npm run type-check              # vue-tsc
```

## Git Conventions

Use conventional commits: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`.
