import sqlite3
import tempfile
import unittest
from pathlib import Path

from notescos.store import MIGRATIONS, NoteError, NoteStore, default_home, normalize_due


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "notes.db"
        self.ticks = iter(f"2026-10-08T10:00:{n:02d}+00:00" for n in range(60))
        self.store = NoteStore(self.path, clock=lambda: next(self.ticks))
        self.addCleanup(self.store.close)

    def test_add_returns_note_with_defaults(self):
        note = self.store.add("Call Sara about the quote")
        self.assertEqual(note["id"], 1)
        self.assertEqual(note["type"], "task")
        self.assertEqual(note["status"], "open")
        self.assertEqual(note["priority"], 0)
        self.assertEqual(note["tags"], [])
        self.assertTrue(note["confirmed"])
        self.assertEqual(note["created_at"], note["updated_at"])

    def test_add_stores_optional_fields(self):
        note = self.store.add(
            "Send invoice", type="followup", due="2026-10-10", priority=2,
            alert_level="urgent", person="Ali", project="acme", tags=["billing"],
        )
        self.assertEqual(
            (note["type"], note["due_at"], note["priority"], note["alert_level"],
             note["person"], note["project"], note["tags"]),
            ("followup", "2026-10-10", 2, "urgent", "Ali", "acme", ["billing"]),
        )

    def test_rejects_bad_input(self):
        for kwargs in (
            {"text": "   "},
            {"text": "x", "type": "bogus"},
            {"text": "x", "alert_level": "loud"},
            {"text": "x", "priority": 9},
            {"text": "x", "due": "next friday"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(NoteError):
                self.store.add(**kwargs)
        self.assertEqual(self.store.list(status=None), [])

    def test_sql_injection_is_inert(self):
        evil = "x'); DROP TABLE notes; --"
        self.store.add(evil, person=evil)
        self.assertEqual(self.store.list()[0]["text"], evil)

    def test_list_orders_by_due_then_id_with_undated_last(self):
        self.store.add("no date")
        self.store.add("later", due="2026-10-20")
        self.store.add("sooner", due="2026-10-09T09:00")
        self.assertEqual([n["text"] for n in self.store.list()], ["sooner", "later", "no date"])

    def test_list_filters(self):
        self.store.add("a", project="p1", type="idea")
        self.store.add("b", project="p2")
        done = self.store.add("c", project="p1")
        self.store.done(done["id"])
        self.assertEqual([n["text"] for n in self.store.list()], ["a", "b"])
        self.assertEqual([n["text"] for n in self.store.list(project="p1")], ["a"])
        self.assertEqual([n["text"] for n in self.store.list(type="idea")], ["a"])
        self.assertEqual(len(self.store.list(status=None)), 3)
        self.assertEqual([n["text"] for n in self.store.list(status="done")], ["c"])

    def test_done_sets_status_and_is_repeatable(self):
        note = self.store.add("ship it")
        finished = self.store.done(note["id"])
        self.assertEqual(finished["status"], "done")
        self.assertIsNotNone(finished["done_at"])
        again = self.store.done(note["id"])
        self.assertEqual(again["done_at"], finished["done_at"])

    def test_unknown_id(self):
        with self.assertRaises(NoteError):
            self.store.get(99)
        with self.assertRaises(NoteError):
            self.store.done(99)

    def test_data_persists_and_migration_is_idempotent(self):
        self.store.add("persist me")
        self.store.close()
        again = NoteStore(self.path)
        self.addCleanup(again.close)
        self.assertEqual(again.list()[0]["text"], "persist me")
        version = again.conn.execute("PRAGMA user_version").fetchone()[0]
        self.assertEqual(version, len(MIGRATIONS))

    def test_refuses_database_from_newer_version(self):
        self.store.close()
        raw = sqlite3.connect(str(self.path))
        raw.execute(f"PRAGMA user_version = {len(MIGRATIONS) + 1}")
        raw.close()
        with self.assertRaises(NoteError):
            NoteStore(self.path)

    def test_normalize_due(self):
        self.assertEqual(normalize_due("2026-10-09"), "2026-10-09")
        self.assertEqual(normalize_due("2026-10-09T15:30"), "2026-10-09T15:30")
        with self.assertRaises(NoteError):
            normalize_due("2026-10-09T15:30+05:00")

    def test_default_home_honours_env(self):
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {"NOTESCOS_HOME": self.tmp.name}):
            self.assertEqual(default_home(), Path(self.tmp.name))
