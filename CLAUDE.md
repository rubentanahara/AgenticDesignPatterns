# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Runnable examples for the 21 chapters + appendices of *Agentic Design Patterns* (book not in repo: copyrighted, gitignored as `AgenticDesignPatternsBook.md`). One folder per chapter (`NN-name/`), each with `README.md` (pattern summary, non-obvious details) and standalone scripts. One root `requirements.txt` covers every chapter. Root `README.md` has the chapter index. Stack: Google ADK (`*_adk.py`) and LangChain/LangGraph on Gemini. Chapters often pair a LangChain script with an ADK script showing the same pattern.

## Commands

No build or test suite. CI (`.github/workflows/offline-checks.yml`) runs `compileall` plus the offline scripts below on push/PR; `.github/dependabot.yml` bumps pip and Actions weekly. Scripts are run directly; a Pyright config exists (`pyrightconfig.json`, venv `~/.venvs/adp`).

```bash
make run CH=02 FILE=router.py   # FILE optional if chapter has one script
PYTHONPATH=. python 01-prompt-chaining/chain.py   # equivalent
```

- `PYTHONPATH` must be repo root so scripts can `from step_logger import ...`.
- Shared venv lives outside the repo (iCloud sync): `~/.venvs/adp`, Python 3.12. Makefile uses it if present, else `python3`; override with `PYTHON=`.
- Needs `GOOGLE_API_KEY` (Gemini). Free tier hits 429 on fan-out chapters (03, 21); wait a minute and retry.
- Model name is a `MODEL` constant at top of each script; change it when models retire.
- Offline (no key): `08-memory-management/state_scopes_adk.py`, `10-model-context-protocol/discover.py`, `19-evaluation-and-monitoring/trajectory_metrics.py`.
- Ch 15 needs two terminals: `weather_server.py` then `trip_planner_client.py`. Ch 24 `review_staged.py` runs inside a git repo with staged changes.
- Ch 23 has no scripts (README only), so `make run CH=23` stops with a message.

## Architecture

- `step_logger.py` (repo root) is the only shared code: `phase` (rule), `show` (panel), `show_event` (ADK events), `StepLogger().step` (LCEL tap). Every script uses it to print pattern phases with `rich`.
- Scripts are self-contained per chapter; no cross-chapter imports besides `step_logger`.
- ADK scripts run via `InMemoryRunner` with `asyncio`. Gotchas already hit in this repo:
  - google-adk 2.13.0 deprecates `ParallelAgent`/`SequentialAgent`; ch 03 `parallel_adk.py` uses `google.adk.workflow` (`Workflow`, fan-out tuple, `JoinNode`) and passes it as `node=` to the runner.
  - Context caching needs the root agent wrapped in `App` with `ContextCacheConfig` (ch 02 `router_adk.py`).
  - Multi-agent transfers in one shared session ping-pong forever; ch 02 sets sub-agents to disallow transfer to parent/peers and runs each request in its own session.
- LangChain `with_structured_output(...)` return type is `BaseModel | dict`; scripts `cast(...)` it to the schema to satisfy Pyright (`router.py`, `reflection.py`).
- Ch 05 `tool_adk.py` calls live Open-Meteo (keyless) for weather.

## Conventions

- Don't commit `__pycache__`, `.DS_Store`, venvs, secrets (root `.gitignore` covers them).
- Python files carry no explanatory comments (stripped repo-wide). Don't add new ones.
- Code is MIT (`LICENSE`). The book is copyrighted and gitignored (`AgenticDesignPatternsBook.md`); never commit it or long excerpts from it.
