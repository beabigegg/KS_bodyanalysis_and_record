from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class SettingsError(ValueError):
    """Raised when config.yaml is invalid."""


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



def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SettingsError(f"'{field_name}' must be a mapping.")
    return value



def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SettingsError(f"'{field_name}' must be a non-empty string.")
    return value.strip()



def _require_positive_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise SettingsError(f"'{field_name}' must be a positive integer.")
    return value



def _require_positive_number(value: Any, field_name: str) -> float:
    if not isinstance(value, (int, float)) or value <= 0:
        raise SettingsError(f"'{field_name}' must be a positive number.")
    return float(value)



def load_settings(config_path: str | Path = "config.yaml") -> AppSettings:
    config_file = Path(config_path)
    if not config_file.exists():
        raise SettingsError(f"Config file does not exist: {config_file}")

    with config_file.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}

    root = _require_mapping(data, "root")

    raw_watch_paths = root.get("watch_paths")
    if not isinstance(raw_watch_paths, list) or not raw_watch_paths:
        raise SettingsError("'watch_paths' must be a non-empty list of paths.")
    watch_paths = [Path(_require_string(item, "watch_paths[]")) for item in raw_watch_paths]

    mysql_map = _require_mapping(root.get("mysql"), "mysql")
    mysql = MySQLConfig(
        host=_require_string(mysql_map.get("host"), "mysql.host"),
        port=_require_positive_int(mysql_map.get("port"), "mysql.port"),
        user=_require_string(mysql_map.get("user"), "mysql.user"),
        password=_require_string(mysql_map.get("password"), "mysql.password"),
        database=_require_string(mysql_map.get("database"), "mysql.database"),
        charset=_require_string(mysql_map.get("charset", "utf8mb4"), "mysql.charset"),
    )

    debounce_map = _require_mapping(root.get("debounce"), "debounce")
    debounce = DebounceConfig(
        settle_seconds=_require_positive_number(
            debounce_map.get("settle_seconds"), "debounce.settle_seconds"
        ),
        poll_seconds=_require_positive_number(
            debounce_map.get("poll_seconds"), "debounce.poll_seconds"
        ),
        stable_checks=_require_positive_int(
            debounce_map.get("stable_checks"), "debounce.stable_checks"
        ),
    )

    scan_interval = _require_positive_int(root.get("scan_interval"), "scan_interval")
    log_file = Path(_require_string(root.get("log_file", "logs/recipe_import.log"), "log_file"))
    state_file = Path(_require_string(root.get("state_file", "state/processed_files.json"), "state_file"))

    return AppSettings(
        watch_paths=watch_paths,
        mysql=mysql,
        debounce=debounce,
        scan_interval=scan_interval,
        log_file=log_file,
        state_file=state_file,
    )
