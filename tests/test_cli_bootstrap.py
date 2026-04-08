from __future__ import annotations

import sys

from ksbody import __main__ as entry


def test_main_pipeline_bootstraps_before_run(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(sys, "argv", ["ksbody", "pipeline"])
    monkeypatch.setattr(entry, "ensure_schema", lambda: calls.append("bootstrap"))
    monkeypatch.setattr(entry, "run_pipeline", lambda process_file=None: calls.append(f"pipeline:{process_file}"))

    entry.main()

    assert calls == ["bootstrap", "pipeline:None"]


def test_main_web_bootstraps_before_run(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(sys, "argv", ["ksbody", "web"])
    monkeypatch.setattr(entry, "ensure_schema", lambda: calls.append("bootstrap"))
    monkeypatch.setattr(entry, "_run_web", lambda: calls.append("web"))

    entry.main()

    assert calls == ["bootstrap", "web"]


def test_main_all_bootstraps_before_process_manager(monkeypatch) -> None:
    calls: list[str] = []

    class _Manager:
        def run(self) -> None:
            calls.append("all")

    monkeypatch.setattr(sys, "argv", ["ksbody", "all"])
    monkeypatch.setattr(entry, "ensure_schema", lambda: calls.append("bootstrap"))
    monkeypatch.setattr(entry, "ProcessManager", _Manager)

    entry.main()

    assert calls == ["bootstrap", "all"]
