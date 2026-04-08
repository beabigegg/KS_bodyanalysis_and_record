from __future__ import annotations

from dataclasses import dataclass
import logging
import multiprocessing as mp
import signal
import time
from types import FrameType
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen


@dataclass
class ManagedProcess:
    name: str
    target: Callable[[], None]
    process: mp.Process | None = None
    start_time: float = 0.0
    restart_count: int = 0
    disabled: bool = False
    next_http_check_at: float = 0.0


class ProcessManager:
    def __init__(
        self,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        max_restarts: int = 5,
        stable_seconds: float = 120.0,
        health_interval: float = 10.0,
        web_health_interval: float = 30.0,
        web_grace_period: float = 15.0,
    ) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_restarts = max_restarts
        self.stable_seconds = stable_seconds
        self.health_interval = health_interval
        self.web_health_interval = web_health_interval
        self.web_grace_period = web_grace_period

        self.logger = logging.getLogger("ksbody.manager")
        self._running = True
        self._ctx = mp.get_context("spawn")
        self._children: dict[str, ManagedProcess] = {
            "pipeline": ManagedProcess(name="pipeline", target=self._run_pipeline),
            "web": ManagedProcess(name="web", target=self._run_web),
        }

    @staticmethod
    def _run_pipeline() -> None:
        from ksbody.pipeline.runner import run_pipeline

        run_pipeline()

    @staticmethod
    def _run_web() -> None:
        import uvicorn

        from ksbody.config import get_settings

        settings = get_settings()
        log_level = "debug" if settings.debug else "info"
        uvicorn.run(
            "ksbody.web.app:app",
            host=settings.app_host,
            port=settings.app_port,
            reload=False,
            log_level=log_level,
        )

    def _handle_signal(self, signum: int, frame: FrameType | None) -> None:
        _ = frame
        self.logger.info("received signal %s, shutting down", signum)
        self._running = False

    def _register_signals(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _spawn(self, child: ManagedProcess) -> None:
        process = self._ctx.Process(target=child.target, name=f"ksbody-{child.name}")
        process.start()
        child.process = process
        child.start_time = time.monotonic()
        if child.name == "web":
            child.next_http_check_at = child.start_time + self.web_grace_period
        self.logger.info("started %s pid=%s", child.name, process.pid)

    def _shutdown_child(self, child: ManagedProcess) -> None:
        if child.process is None:
            return
        proc = child.process
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=10)
            if proc.is_alive():
                self.logger.warning("%s did not stop in time; killing", child.name)
                proc.kill()
                proc.join(timeout=3)
        child.process = None

    def _is_web_healthy(self) -> bool:
        try:
            from ksbody.config import get_settings

            settings = get_settings()
            url = f"http://{settings.app_host}:{settings.app_port}/api/health"
            with urlopen(url, timeout=5) as resp:  # nosec B310
                return resp.status == 200
        except (URLError, TimeoutError, OSError):
            return False

    def _restart(self, child: ManagedProcess, reason: str) -> None:
        now = time.monotonic()
        runtime = now - child.start_time
        if runtime >= self.stable_seconds:
            child.restart_count = 0

        child.restart_count += 1
        if child.restart_count > self.max_restarts:
            child.disabled = True
            self.logger.critical(
                "%s restart limit exceeded (%s), disabling process",
                child.name,
                self.max_restarts,
            )
            return

        delay = min(self.base_delay * (2 ** (child.restart_count - 1)), self.max_delay)
        self.logger.warning(
            "%s unhealthy (%s), restarting in %.1fs (%s/%s)",
            child.name,
            reason,
            delay,
            child.restart_count,
            self.max_restarts,
        )
        self._shutdown_child(child)
        time.sleep(delay)
        self._spawn(child)

    def _check_child(self, child: ManagedProcess, now: float) -> None:
        if child.disabled or child.process is None:
            return

        if not child.process.is_alive():
            code = child.process.exitcode
            self._restart(child, f"exit_code={code}")
            return

        if child.name == "web" and now >= child.next_http_check_at:
            if not self._is_web_healthy():
                self._restart(child, "web_health_check_failed")
                return
            child.next_http_check_at = now + self.web_health_interval

    def run(self) -> None:
        self._register_signals()
        for child in self._children.values():
            self._spawn(child)

        try:
            while self._running:
                now = time.monotonic()
                for child in self._children.values():
                    self._check_child(child, now)
                time.sleep(self.health_interval)
        finally:
            for child in self._children.values():
                self._shutdown_child(child)
            self.logger.info("all child processes stopped")