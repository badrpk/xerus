"""Standalone disk-first memory for Xerus.

The filesystem JSONL journal is authoritative. Search is local and bounded.
No network service or external database is required.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()


def _root() -> Path:
    return Path(
        os.environ.get(
            "XERUS_HOME",
            Path.home() / ".local/share/xerus",
        )
    ).expanduser()


def _journal() -> Path:
    return _root() / "memory.jsonl"


def _make_key(*, namespace: str, content: str, metadata: dict[str, Any]) -> str:
    payload = namespace + "\0" + content + "\0" + json.dumps(
        metadata,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()[:32]


def remember(
    content: str,
    *,
    namespace: str = "general",
    memory_key: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = str(content or "").strip()
    if not value:
        return {"ok": False, "reason": "empty content"}

    namespace = str(namespace or "").strip() or "general"
    metadata_value = dict(metadata or {})
    key = str(memory_key).strip() if memory_key else _make_key(
        namespace=namespace,
        content=value,
        metadata=metadata_value,
    )

    record = {
        "ts": time.time(),
        "memory_key": key,
        "namespace": namespace,
        "content": value,
        "metadata": metadata_value,
    }

    with _LOCK:
        journal = _journal()
        journal.parent.mkdir(parents=True, exist_ok=True)
        with journal.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    return {
        "ok": True,
        "memory_key": key,
        "backend": "filesystem-journal",
        "path": str(_journal()),
    }


def recall(
    query: str,
    *,
    namespace: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    journal = _journal()
    if not journal.exists():
        return []

    terms = {item.casefold() for item in str(query).split() if item.strip()}
    limit = max(1, min(int(limit), 50))

    try:
        lines = journal.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    latest_by_key: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []

    for line in lines[-10000:]:
        try:
            item = json.loads(line)
        except Exception:
            continue
        if not isinstance(item, dict):
            continue

        key = str(item.get("memory_key", "") or "").strip()
        if key:
            latest_by_key[key] = item
        else:
            anonymous.append(item)

    scored: list[tuple[int, float, dict[str, Any]]] = []
    for item in [*latest_by_key.values(), *anonymous]:
        if namespace and item.get("namespace") != namespace:
            continue

        content = str(item.get("content", ""))
        lowered = content.casefold()
        score = sum(1 for term in terms if term in lowered)
        if not score:
            continue

        scored.append((
            score,
            float(item.get("ts", 0.0) or 0.0),
            {**item, "source": "filesystem-journal"},
        ))

    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [item for _, _, item in scored[:limit]]


def status() -> dict[str, Any]:
    journal = _journal()
    return {
        "ok": True,
        "backend": "filesystem-journal",
        "path": str(journal),
        "exists": journal.exists(),
        "bytes": journal.stat().st_size if journal.exists() else 0,
        "disk_first": True,
    }
