from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable


class JournalError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryRecord:
    key: str
    value: Any
    sequence: int
    previous_hash: str
    record_hash: str

    def body(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "sequence": self.sequence,
            "previous_hash": self.previous_hash,
        }


class MemoryJournal:
    """Append-only, disk-first JSONL memory journal with deterministic hash chaining."""

    GENESIS = "0" * 64

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @staticmethod
    def stable_key(namespace: str, subject: str) -> str:
        namespace = namespace.strip()
        subject = subject.strip()
        if not namespace or not subject:
            raise JournalError("namespace and subject are required")
        return _hash({"namespace": namespace, "subject": subject})

    def _records(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        records: list[MemoryRecord] = []
        previous = self.GENESIS
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JournalError(f"invalid JSON at line {line_number}") from exc
            required = {"key", "value", "sequence", "previous_hash", "record_hash"}
            if set(raw) != required:
                raise JournalError(f"invalid record shape at line {line_number}")
            body = {
                "key": raw["key"],
                "value": raw["value"],
                "sequence": raw["sequence"],
                "previous_hash": raw["previous_hash"],
            }
            if raw["previous_hash"] != previous:
                raise JournalError(f"hash chain mismatch at line {line_number}")
            expected = _hash(body)
            if raw["record_hash"] != expected:
                raise JournalError(f"record checksum mismatch at line {line_number}")
            if raw["sequence"] != len(records) + 1:
                raise JournalError(f"sequence mismatch at line {line_number}")
            record = MemoryRecord(record_hash=expected, **body)
            records.append(record)
            previous = expected
        return records

    def remember(self, key: str, value: Any) -> MemoryRecord:
        key = key.strip()
        if not key:
            raise JournalError("key is required")
        records = self._records()
        previous = records[-1].record_hash if records else self.GENESIS
        body = {
            "key": key,
            "value": value,
            "sequence": len(records) + 1,
            "previous_hash": previous,
        }
        record = MemoryRecord(record_hash=_hash(body), **body)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(_canonical(asdict(record)) + "\n")
        return record

    def recall(self, key: str, default: Any = None) -> Any:
        for record in reversed(self._records()):
            if record.key == key:
                return record.value
        return default

    def replay(self) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for record in self._records():
            state[record.key] = record.value
        return state

    def records(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._records())

    def verify(self) -> bool:
        self._records()
        return True

    def manifest(self) -> dict[str, Any]:
        records = self._records()
        state = self.replay()
        manifest = {
            "format": "xerus-memory-journal-v1",
            "records": len(records),
            "head": records[-1].record_hash if records else self.GENESIS,
            "state": state,
        }
        return {**manifest, "manifest_hash": _hash(manifest)}

    def compact_snapshot(self, destination: str | Path) -> dict[str, Any]:
        snapshot = self.manifest()
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(_canonical(snapshot) + "\n", encoding="utf-8")
        return snapshot


def replay_records(records: Iterable[MemoryRecord]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for record in records:
        state[record.key] = record.value
    return state
