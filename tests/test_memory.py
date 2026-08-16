from __future__ import annotations

import json
from pathlib import Path

from xerus.memory import recall, remember, status


def test_disk_first_round_trip(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("XERUS_HOME", str(tmp_path))

    first = remember(
        "alpha persistent memory",
        namespace="demo",
        memory_key="shared-key",
        metadata={"version": 1},
    )
    assert first["ok"] is True

    second = remember(
        "beta persistent memory",
        namespace="demo",
        memory_key="shared-key",
        metadata={"version": 2},
    )
    assert second["ok"] is True

    remember("other namespace memory", namespace="other")

    hits = recall("persistent memory", namespace="demo", limit=10)
    assert len(hits) == 1
    assert hits[0]["memory_key"] == "shared-key"
    assert hits[0]["content"] == "beta persistent memory"
    assert hits[0]["metadata"]["version"] == 2

    info = status()
    assert info["disk_first"] is True
    assert info["backend"] == "filesystem-journal"
    assert info["exists"] is True

    journal = tmp_path / "memory.jsonl"
    rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
