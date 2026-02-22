# SousChefAI Backend

Python 3.12 FastAPI backend with async SQLAlchemy, Pydantic Settings, and pluggable AI providers.

## Tech Stack

- **Framework**: FastAPI with uvicorn
- **Database**: SQLite via async SQLAlchemy + aiosqlite
- **Migrations**: Alembic
- **Config**: Pydantic Settings with hierarchical sources
- **Auth**: JWT (python-jose) + OAuth2 (Google, Facebook)
- **AI**: Ollama, Anthropic, OpenAI, Claude Code CLI
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: ruff (format + lint), pyright (types), bandit (security)

## Key Files

```
app/
  config.py          # Settings with hierarchical config
  main.py            # FastAPI app, CORS, router registration
  __main__.py        # CLI entry point
  database.py        # Async engine, session factory, Base
  api/               # Route handlers
    auth.py, users.py, ingredients.py, recipes.py, household.py, shopping.py, ai.py
    deps.py          # Shared dependencies (get_db, get_current_user)
  models/            # SQLAlchemy ORM models
    user.py, ingredient.py, recipe.py, household.py, shopping.py
  schemas/           # Pydantic request/response schemas
    user.py, ingredient.py, recipe.py, household.py, shopping.py, ai.py, legal.py
  services/
    auth.py          # Auth business logic
    barcode.py       # OpenFoodFacts barcode lookup
    ai/              # AI provider implementations
      base.py        # AIService ABC
      __init__.py    # get_ai_service() factory
      ollama.py, anthropic.py, openai_service.py, claude_local.py
  utils/
    security.py      # JWT token creation/verification
alembic/             # Database migrations
tests/
  unit/              # Unit tests
  integration/       # Integration tests
  conftest.py        # Shared fixtures
```

## Configuration System

Defined in `app/config.py`. Priority (highest first):

1. **CLI args**: `python -m app --port=8000 --ai-provider=anthropic`
2. **Secrets files**: `/run/secrets` or `/etc/secrets` (auto-discovered)
3. **Environment variables**: `PORT=8000`
4. **.env file**: loaded automatically
5. **Defaults**: hardcoded in `Settings` class

To add a new setting: add a field to `Settings` in `config.py`. It automatically becomes available from all sources. CLI uses kebab-case (`--my-setting`), env uses UPPER_SNAKE (`MY_SETTING`).

## AI Service Pattern

Abstract base class in `app/services/ai/base.py` with 4 methods:
- `generate_recipes()` - Recipe generation from ingredients
- `identify_ingredients_from_image()` - Vision/image analysis
- `suggest_substitutions()` - Ingredient alternatives
- `parse_voice_input()` - Voice transcript parsing

Factory in `app/services/ai/__init__.py`: `get_ai_service()` returns the provider based on `settings.ai_provider`.

### Adding a New AI Provider

1. Create `app/services/ai/my_provider.py` implementing `AIService` ABC
2. Add enum value to `AIProvider` in `config.py`
3. Add import branch in `get_ai_service()` in `app/services/ai/__init__.py`
4. Add any config fields (API keys, model names) to `Settings`

## Database

Async SQLAlchemy with `aiosqlite`. Engine and session factory in `app/database.py`. Models inherit from `Base`.

```bash
# Create migration after model changes
alembic revision --autogenerate -m "add foo table"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

Tables auto-create on startup via `init_db()` in the FastAPI lifespan.

## API Routes

All routes prefixed with `/api`:

| Prefix               | Module          | Purpose                    |
|-----------------------|-----------------|----------------------------|
| `/api/auth`          | `api/auth.py`   | Register, login, OAuth     |
| `/api/users`         | `api/users.py`  | Profile, preferences       |
| `/api/ingredients`   | `api/ingredients.py` | Pantry, barcode, camera |
| `/api/recipes`       | `api/recipes.py`| Search, rate, favorites    |
| `/api/household`     | `api/household.py` | Family, members         |
| `/api/shopping`      | `api/shopping.py` | Shopping carts, items    |
| `/api/ai`            | `api/ai.py`     | AI providers, voice, subs  |
| `/api/health`        | `main.py`       | Health check               |

## Commands

```bash
# Run server
python -m app                              # default: 0.0.0.0:6000
python -m app --port=8000 --debug          # custom port, debug mode

# Tests
pytest                                     # all tests
pytest tests/unit/                         # unit only
pytest tests/integration/                  # integration only
pytest --cov=app --cov-report=term-missing # with coverage

# Linting
ruff check .                               # lint check
ruff check . --fix                         # lint fix
ruff format .                              # format
ruff format . --check                      # format check
pyright                                    # type check
bandit -r app/                             # security scan
```
