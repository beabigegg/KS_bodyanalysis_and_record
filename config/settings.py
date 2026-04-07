from __future__ import annotations

from dataclasses import dataclass
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
class AppSettings:
    watch_paths: list[Path]
    mysql: MySQLConfig
    debounce: DebounceConfig
    scan_interval: int
    log_file: Path
    state_file: Path


def _load_env() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")


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
    raw = _require_env("WATCH_PATHS")
    paths = [Path(item.strip()) for item in raw.split(",") if item.strip()]
    if not paths:
        raise SettingsError("WATCH_PATHS must contain at least one path.")
    return paths


def load_settings() -> AppSettings:
    _load_env()

    mysql = MySQLConfig(
        host=_require_env("MYSQL_HOST"),
        port=_parse_positive_int("MYSQL_PORT"),
        user=_require_env("MYSQL_USER"),
        password=_require_env("MYSQL_PASSWORD"),
        database=_require_env("MYSQL_DATABASE"),
        charset=os.getenv("MYSQL_CHARSET", "utf8mb4").strip() or "utf8mb4",
    )

    debounce = DebounceConfig(
        settle_seconds=_parse_positive_float("DEBOUNCE_SETTLE_SECONDS", 5.0),
        poll_seconds=_parse_positive_float("DEBOUNCE_POLL_SECONDS", 1.0),
        stable_checks=_parse_positive_int("DEBOUNCE_STABLE_CHECKS", default=2),
    )

    return AppSettings(
        watch_paths=_parse_watch_paths(),
        mysql=mysql,
        debounce=debounce,
        scan_interval=_parse_positive_int("SCAN_INTERVAL", default=300),
        log_file=Path(os.getenv("LOG_FILE", "logs/recipe_import.log").strip()),
        state_file=Path(os.getenv("STATE_FILE", "state/processed_files.json").strip()),
    )
