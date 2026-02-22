# Hierarchical Config Loader & CLAUDE.md Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the flat Pydantic Settings config with a hierarchical loader (env -> secrets -> CLI) and create comprehensive CLAUDE.md files for the project.

**Architecture:** Extend `app/config.py` using Pydantic Settings v2's `settings_customise_sources` hook to chain 4 built-in sources: dotenv, env vars, secrets files, and CLI args. Each source overrides the previous. A `__main__.py` entry point enables CLI usage.

**Tech Stack:** pydantic-settings v2.13+ (CliSettingsSource, SecretsSettingsSource, EnvSettingsSource), Python 3.12, FastAPI, Vue 3/Vite

---

### Task 1: Fix missing pydantic[email] dependency

**Files:**
- Modify: `backend/pyproject.toml:6` (dependencies list)

**Step 1: Add email-validator to dependencies**

In `backend/pyproject.toml`, change `"pydantic>=2.10.0"` to `"pydantic[email]>=2.10.0"` in the dependencies list.

**Step 2: Verify install**

Run: `cd backend && source .venv/Scripts/activate && pip install -e ".[dev]"`
Expected: Successfully installed (email-validator already present from earlier manual install)

**Step 3: Commit**

```
git add backend/pyproject.toml
git commit -m "fix: add pydantic[email] to dependencies for EmailStr support"
```

---

### Task 2: Add hierarchical config loader to app/config.py

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/tests/unit/test_config.py`

**Step 1: Write failing tests for the hierarchical config**

Replace `backend/tests/unit/test_config.py` with tests covering:
- Default settings with `cli_parse_args=[]` (no CLI in tests)
- New `port` (default 6000) and `host` (default "0.0.0.0") fields
- Env var overrides default (set `AI_PROVIDER=anthropic` in env)
- CLI overrides env var (pass `--ai_provider=openai` via `cli_parse_args`)
- Secrets dir overrides env var (write file to tmp_path, pass `_secrets_dir`)
- CLI overrides secrets (highest priority)
- Missing secrets dir handled gracefully (non-existent path)
- Port configurable via CLI (`--port=9999`)
- Port configurable via env var (`PORT=8888`)

**Step 2: Run tests to verify they fail**

Run: `cd backend && source .venv/Scripts/activate && python -m pytest tests/unit/test_config.py -v`
Expected: FAIL -- Settings doesn't accept cli_parse_args yet, no port/host fields

**Step 3: Implement the hierarchical config in app/config.py**

Replace `backend/app/config.py` with:
- Import CliSettingsSource, SecretsSettingsSource, PydanticBaseSettingsSource
- Add `_SECRETS_DIRS = [Path("/run/secrets"), Path("/etc/secrets")]`
- Add `_find_secrets_dir()` helper that returns first existing dir or None
- Update `model_config` to include `cli_parse_args=True`, `cli_ignore_unknown_args=True`, `cli_kebab_case=True`
- Add `host: str = "0.0.0.0"` and `port: int = 6000` fields
- Update `allowed_origins` default to `["http://localhost:6001"]`
- Update `oauth_redirect_base_url` default to `"http://localhost:6000"`
- Override `settings_customise_sources` with priority: CLI > secrets > env > dotenv > init

**Step 4: Run tests to verify they pass**

Run: `cd backend && source .venv/Scripts/activate && python -m pytest tests/unit/test_config.py -v`
Expected: ALL PASS

**Step 5: Run full test suite for regressions**

Run: `cd backend && source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 6: Commit**

```
git add backend/app/config.py backend/tests/unit/test_config.py
git commit -m "feat: add hierarchical config loader (env -> secrets -> CLI)"
```

---

### Task 3: Create CLI entry point (__main__.py)

**Files:**
- Create: `backend/app/__main__.py`

**Step 1: Create the entry point**

Create `backend/app/__main__.py` with a `main()` function that:
- Imports settings from app.config
- Calls `uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)`
- Has `if __name__ == "__main__": main()` guard

**Step 2: Test the entry point**

Run: `cd backend && source .venv/Scripts/activate && python -m app --help`
Expected: Shows CLI args for all Settings fields

**Step 3: Commit**

```
git add backend/app/__main__.py
git commit -m "feat: add CLI entry point (python -m app --port=6000)"
```

---

### Task 4: Fix claude_local.py hardcoded model

**Files:**
- Modify: `backend/app/services/ai/claude_local.py`
- Modify: `backend/tests/unit/test_claude_local_service.py`

**Step 1: Write a failing test for configurable model**

Add test to `backend/tests/unit/test_claude_local_service.py` that:
- Monkeypatches `app.services.ai.claude_local.settings` with `claude_local_model="test-model-123"`
- Mocks `asyncio.create_subprocess_exec` to capture args
- Calls `service._run_claude("test prompt")`
- Asserts `"test-model-123"` appears in the captured subprocess args

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/Scripts/activate && python -m pytest tests/unit/test_claude_local_service.py -v -k "test_claude_local_uses_settings_model"`
Expected: FAIL -- hardcoded model doesn't match

**Step 3: Fix the hardcoded model**

In `backend/app/services/ai/claude_local.py`:
- Add `from app.config import settings` import
- Replace hardcoded `"claude-sonnet-4-20250514"` on line 18 with `settings.claude_local_model`

**Step 4: Run tests to verify**

Run: `cd backend && source .venv/Scripts/activate && python -m pytest tests/unit/test_claude_local_service.py -v`
Expected: ALL PASS

**Step 5: Commit**

```
git add backend/app/services/ai/claude_local.py backend/tests/unit/test_claude_local_service.py
git commit -m "fix: use settings.claude_local_model instead of hardcoded model"
```

---

### Task 5: Update .env files with ports and Claude Code settings

**Files:**
- Modify: `backend/.env`
- Modify: `backend/.env.example`
- Create: `frontend/.env.example`

**Step 1: Update both backend .env files**

Add `HOST=0.0.0.0` and `PORT=6000` at top. Add commented Claude Code section:
```
# --- Claude Code (local CLI) ---
# To use Claude Code as AI provider, uncomment the next two lines:
# AI_PROVIDER=claude_local
# CLAUDE_LOCAL_MODEL=claude-sonnet-4-20250514
```

**Step 2: Create frontend/.env.example**

Minimal file explaining that API is proxied via vite.config.ts.

**Step 3: Commit**

```
git add backend/.env.example frontend/.env.example
git commit -m "chore: update .env templates with ports and Claude Code settings"
```

Note: `backend/.env` is gitignored and not committed.

---

### Task 6: Update docker-compose.yml for new ports

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Update ports**

Change backend port mapping to `"6000:6000"` and command to use `--port 6000`.
Change frontend port mapping to `"6001:80"`.

**Step 2: Commit**

```
git add docker-compose.yml
git commit -m "chore: update docker-compose ports to 6000/6001"
```

---

### Task 7: Create CLAUDE.md files

**Files:**
- Create: `CLAUDE.md` (project root)
- Create: `backend/CLAUDE.md`
- Create: `frontend/CLAUDE.md`

**Step 1: Verify CLAUDE.md is not gitignored**

Run: `git check-ignore CLAUDE.md backend/CLAUDE.md frontend/CLAUDE.md`
Expected: No output (none are ignored)

**Step 2: Create root CLAUDE.md**

Cover: project purpose, monorepo structure, dev setup, ports (6000/6001/11434), hierarchical config system, AI providers, database, testing commands, linting, key directories.

**Step 3: Create backend/CLAUDE.md**

Cover: Python 3.12+, FastAPI, config system details, AI service pattern, database, auth, API routes, services, run/test/lint commands.

**Step 4: Create frontend/CLAUDE.md**

Cover: Vue 3 + Composition API + TypeScript + Vite, Pinia, vue-router, API layer, Capacitor, run/test/lint commands, component patterns.

**Step 5: Commit**

```
git add CLAUDE.md backend/CLAUDE.md frontend/CLAUDE.md
git commit -m "docs: add CLAUDE.md project context files for Claude Code"
```

---

### Task 8: Verify everything works end-to-end

**Step 1: Run backend tests**

Run: `cd backend && source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 2: Run frontend tests**

Run: `cd frontend && npm run test`
Expected: ALL PASS

**Step 3: Run linters**

Run: `cd backend && source .venv/Scripts/activate && ruff check .`
Run: `cd frontend && npm run lint:check`
Expected: No errors

**Step 4: Verify git tracking**

Run: `git check-ignore CLAUDE.md backend/CLAUDE.md frontend/CLAUDE.md backend/.env.example frontend/.env.example`
Expected: No output (none ignored)

**Step 5: Start servers and verify**

Run backend on port 6000, frontend on port 6001.
Verify: `curl http://localhost:6000/api/health` returns `{"status":"healthy"}`
Verify: `curl http://localhost:6001` returns HTTP 200

**Step 6: Final commit if any fixups needed**
