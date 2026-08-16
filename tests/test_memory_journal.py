import json
import tempfile
import unittest
from pathlib import Path

from memory.journal import JournalError, MemoryJournal, replay_records


class MemoryJournalTests(unittest.TestCase):
    def make_journal(self):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "memory.jsonl"
        return tmp, MemoryJournal(path)

    def test_stable_key_is_deterministic(self):
        a = MemoryJournal.stable_key("user", "42")
        b = MemoryJournal.stable_key("user", "42")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_remember_and_recall_latest_value(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("theme", "light")
        journal.remember("theme", "dark")
        self.assertEqual(journal.recall("theme"), "dark")

    def test_replay_reconstructs_state(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("a", 1)
        journal.remember("b", 2)
        journal.remember("a", 3)
        self.assertEqual(journal.replay(), {"a": 3, "b": 2})

    def test_record_hash_chain_is_valid(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        one = journal.remember("a", 1)
        two = journal.remember("b", 2)
        self.assertEqual(two.previous_hash, one.record_hash)
        self.assertTrue(journal.verify())

    def test_tampering_is_detected(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("a", 1)
        lines = journal.path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[0])
        record["value"] = 99
        journal.path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaises(JournalError):
            journal.verify()

    def test_sequence_corruption_is_detected(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("a", 1)
        raw = json.loads(journal.path.read_text(encoding="utf-8"))
        raw["sequence"] = 2
        journal.path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
        with self.assertRaises(JournalError):
            journal.verify()

    def test_manifest_is_deterministic_for_same_journal(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("b", {"z": 2, "a": 1})
        self.assertEqual(journal.manifest(), journal.manifest())

    def test_snapshot_matches_manifest(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("a", 1)
        target = Path(tmp.name) / "snapshot.json"
        snapshot = journal.compact_snapshot(target)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), snapshot)

    def test_replay_records_helper(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        journal.remember("a", 1)
        journal.remember("a", 2)
        self.assertEqual(replay_records(journal.records()), {"a": 2})

    def test_missing_key_default(self):
        tmp, journal = self.make_journal()
        self.addCleanup(tmp.cleanup)
        self.assertEqual(journal.recall("missing", "fallback"), "fallback")


if __name__ == "__main__":
    unittest.main()
