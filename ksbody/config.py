from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
import os
from pathlib import Path

from dotenv import load_dotenv


class SettingsError(ValueError):
    """Raised when environment settings are invalid."""


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"

    def sqlalchemy_url(self) -> str:
        return (
            f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/"
            f"{self.database}?charset={self.charset}"
        )


@dataclass(frozen=True)
class DebounceConfig:
    settle_seconds: float
    poll_seconds: float
    stable_checks: int


@dataclass(frozen=True)
class OracleConfig:
    dsn: str
    user: str
    password: str


@dataclass(frozen=True)
class Settings:
    mysql: MySQLConfig
    watch_paths: list[Path]
    debounce: DebounceConfig
    scan_interval: int
    log_file: Path
    state_file: Path
    app_host: str
    app_port: int
    app_mode: str
    app_cors_origins: list[str]
    oracle: OracleConfig | None
    debug: bool


def _load_env() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _require_env(name: str) -> str:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        raise SettingsError(f"Missing required environment variable: {name}")
    return raw.strip()


def _parse_positive_int(name: str, default: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        if default is None:
            raise SettingsError(f"Missing required environment variable: {name}")
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise SettingsError(f"Environment variable {name} must be an integer.") from exc
    if value <= 0:
        raise SettingsError(f"Environment variable {name} must be a positive integer.")
    return value


def _parse_positive_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise SettingsError(f"Environment variable {name} must be a number.") from exc
    if value <= 0:
        raise SettingsError(f"Environment variable {name} must be a positive number.")
    return value


def _parse_watch_paths() -> list[Path]:
    raw = os.getenv("WATCH_PATHS", "")
    return [Path(item.strip()) for item in raw.split(",") if item.strip()]


def _parse_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _build_oracle_config() -> OracleConfig | None:
    dsn = os.getenv("ORACLE_DSN")
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    if dsn and user and password:
        return OracleConfig(dsn=dsn.strip(), user=user.strip(), password=password.strip())
    return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_env()

    mode = os.getenv("APP_MODE", "dev").strip().lower()
    debug = _parse_bool("APP_DEBUG", default=(mode == "dev"))
    _setup_logging(debug)

    mysql = MySQLConfig(
        host=os.getenv("MYSQL_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_parse_positive_int("MYSQL_PORT", default=3306),
        user=os.getenv("MYSQL_USER", "root").strip() or "root",
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "").strip(),
        charset=os.getenv("MYSQL_CHARSET", "utf8mb4").strip() or "utf8mb4",
    )

    debounce = DebounceConfig(
        settle_seconds=_parse_positive_float("DEBOUNCE_SETTLE_SECONDS", 5.0),
        poll_seconds=_parse_positive_float("DEBOUNCE_POLL_SECONDS", 1.0),
        stable_checks=_parse_positive_int("DEBOUNCE_STABLE_CHECKS", default=2),
    )

    cors_raw = os.getenv("APP_CORS_ORIGINS", "http://localhost:5173")
    cors_origins = [item.strip() for item in cors_raw.split(",") if item.strip()]

    return Settings(
        mysql=mysql,
        watch_paths=_parse_watch_paths(),
        debounce=debounce,
        scan_interval=_parse_positive_int("SCAN_INTERVAL", default=300),
        log_file=Path(os.getenv("LOG_FILE", "logs/recipe_import.log").strip()),
        state_file=Path(os.getenv("STATE_FILE", "state/processed_files.json").strip()),
        app_host=os.getenv("APP_HOST", "0.0.0.0").strip() or "0.0.0.0",
        app_port=_parse_positive_int("APP_PORT", default=12010),
        app_mode=mode,
        app_cors_origins=cors_origins,
        oracle=_build_oracle_config(),
        debug=debug,
    )
