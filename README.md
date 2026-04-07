# KS Body Analysis and Record

KS ConnX Elite recipe body analysis project with two services:
- Pipeline service: watches recipe body files, parses content, and writes metadata to MySQL.
- Web service: FastAPI + React UI for querying and visualizing parsed recipe data.

## Architecture

- `main.py`: pipeline entrypoint (watcher + scanner + parser + MySQL persistence)
- `web/app.py`: web entrypoint (FastAPI API + static frontend hosting)
- `config/settings.py`: pipeline environment-based configuration loader
- `web/settings.py`: web environment-based configuration loader

## Installation

### 1. Pipeline dependencies

```bash
pip install -r requirements.txt
```

### 2. Web dependencies

```bash
cd web
pip install -r requirements.txt
cd frontend
npm install
npm run build
```

## Environment Variables

Use root `.env.example` as the source template for both services.

```bash
cp .env.example .env
```

Key groups:
- Pipeline: `WATCH_PATHS`, `DEBOUNCE_*`, `SCAN_INTERVAL`, `LOG_FILE`, `STATE_FILE`
- Shared DB: `MYSQL_*`
- Web app: `APP_*`
- Optional Oracle: `ORACLE_*`
- Recipe trace SMB: `RECIPE_TRACE_SMB_*`

Do not commit `.env` with real credentials.

## Start Commands

### Pipeline

```bash
python main.py
```

Optional one-shot validation:

```bash
python main.py --process-file "<recipe-body-file>"
```

### Web

```bash
cd web
python app.py
```

## Deployment Notes

1. Prepare `.env` from root `.env.example` and fill production secrets.
2. Set web runtime to production (`APP_MODE=prod`, `APP_DEBUG=false`).
3. Build frontend assets (`cd web/frontend && npm run build`).
4. Start pipeline (`python main.py`) and web (`cd web && python app.py`) as separate services.
5. Ensure network access to configured SMB watch path and MySQL server.

## OpenSpec Documentation

PRD/SDD/TDD requirements are tracked in OpenSpec artifacts:
- `openspec/changes/`
- `openspec/specs/`
