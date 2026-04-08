# KS Body Analysis and Record

This repository contains one Python application package, [`ksbody/`](/d:/WORK/user_scrip/TOOL/KS_bodyanalysis_and_record/ksbody), plus the project-level files needed to develop, test, package, and deploy it.

## Structure

- `ksbody/`: application code
- `tests/`: automated tests
- `scripts/`: deployment and maintenance scripts
- `pyproject.toml`: single source of truth for Python dependencies and CLI entrypoints
- `.env.example`: single source of truth for runtime configuration template

## Installation

```bash
pip install -e .
```

Optional Oracle support:

```bash
pip install -e ".[oracle]"
```

Frontend build:

```bash
cd ksbody/web/frontend
npm ci
npm run build
```

## Configuration

Runtime configuration is loaded from the project root `.env`.

```bash
cp .env.example .env
```

Key groups:
- `MYSQL_*`
- `WATCH_PATHS`, `DEBOUNCE_*`, `SCAN_INTERVAL`, `LOG_FILE`, `STATE_FILE`
- `APP_*`
- `ORACLE_*`

Before starting services, make sure `.env` contains:
- reachable `MYSQL_*` connection settings
- valid `WATCH_PATHS`
- optional `APP_PORT` if `12010` is already in use

## Commands

```bash
python -m ksbody pipeline
python -m ksbody pipeline --process-file "<recipe-body-file>"
python -m ksbody web
python -m ksbody all
python -m ksbody init-db
```

After installation, the console script is also available:

```bash
ksbody pipeline
ksbody web
ksbody all
ksbody init-db
```

## Deployment

Full deployment script:

```bash
bash scripts/deploy.sh
```

Behavior:
- prefers conda if available
- falls back to repo-local `.venv` when conda is unavailable
- installs the package in editable mode
- builds frontend assets
- starts `python -m ksbody all` by default

Useful environment flags:

```bash
DEPLOY_START=0 bash scripts/deploy.sh
RUN_NPM_CI=1 bash scripts/deploy.sh
CONDA_ENV_NAME=ksbody bash scripts/deploy.sh
```

- `DEPLOY_START=0`: deploy only, do not start services
- `RUN_NPM_CI=1`: force re-install frontend packages
- `CONDA_ENV_NAME`: choose a different conda env name

## Startup

Start only the web service:

```bash
bash scripts/start-web.sh
scripts\start-web.bat
```

Direct CLI startup:

```bash
python -m ksbody web
python -m ksbody pipeline
python -m ksbody all
```

Validation mode for one recipe archive:

```bash
python -m ksbody pipeline --process-file "<recipe-body-file>"
```

Health check after startup:

```bash
curl http://127.0.0.1:12010/api/health
```

## OpenSpec

- `openspec/changes/`
- `openspec/specs/`
