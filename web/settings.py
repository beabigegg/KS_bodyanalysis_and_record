from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    web_dir = Path(__file__).resolve().parent
    root_dir = web_dir.parent
    load_dotenv(web_dir / ".env")
    load_dotenv(root_dir / ".env")


def _as_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    app_mode: str
    app_cors_origins: list[str]
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    oracle_dsn: str | None
    oracle_user: str | None
    oracle_password: str | None
    debug: bool

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )

    @property
    def oracle_configured(self) -> bool:
        return bool(self.oracle_dsn and self.oracle_user and self.oracle_password)


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_settings() -> Settings:
    _load_env()
    cors_raw = os.getenv("APP_CORS_ORIGINS", "http://localhost:5173")
    cors = [item.strip() for item in cors_raw.split(",") if item.strip()]
    mode = os.getenv("APP_MODE", "dev").strip().lower()
    debug = _as_bool(os.getenv("APP_DEBUG"), default=(mode == "dev"))
    _setup_logging(debug)
    return Settings(
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "12010")),
        app_mode=mode,
        app_cors_origins=cors,
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", "root"),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        mysql_database=os.getenv("MYSQL_DATABASE", ""),
        mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
        oracle_dsn=os.getenv("ORACLE_DSN") or None,
        oracle_user=os.getenv("ORACLE_USER") or None,
        oracle_password=os.getenv("ORACLE_PASSWORD") or None,
        debug=debug,
    )


settings = load_settings()
