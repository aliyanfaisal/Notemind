import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from notescos.brief import build_brief, format_banner, format_today, when_label
from notescos.store import NoteStore

# Thursday 8 Oct 2026, 10:00
NOW = datetime(2026, 10, 8, 10, 0)


class BriefTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = NoteStore(Path(tmp.name) / "notes.db")
        self.addCleanup(self.store.close)

    def add(self, text, due=None, **kwargs):
        return self.store.add(text, due=due, **kwargs)

    def brief(self, **kwargs):
        return build_brief(self.store.list(), NOW, **kwargs)

    def texts(self, group):
        return [n["text"] for n in group]

    def test_sorts_notes_into_groups(self):
        self.add("two days late", "2026-10-06")
        self.add("earlier today", "2026-10-08T09:00")
        self.add("later today", "2026-10-08T15:00")
        self.add("date only today", "2026-10-08")
        self.add("tomorrow", "2026-10-09")
        self.add("in a week", "2026-10-15")
        self.add("far away", "2026-12-01")
        self.add("no date")
        brief = self.brief()
        self.assertEqual(self.texts(brief.overdue), ["two days late", "earlier today"])
        self.assertEqual(self.texts(brief.due_today), ["later today", "date only today"])
        self.assertEqual(self.texts(brief.upcoming), ["tomorrow", "in a week"])
        self.assertEqual(self.texts(brief.undated), ["no date"])

    def test_horizon_limits_upcoming(self):
        self.add("tomorrow", "2026-10-09")
        self.add("in a week", "2026-10-15")
        self.assertEqual(self.texts(self.brief(horizon_days=2).upcoming), ["tomorrow"])

    def test_done_and_silent_notes(self):
        finished = self.add("finished", "2026-10-01")
        self.store.done(finished["id"])
        self.add("quiet one", "2026-10-01", alert_level="silent")
        self.assertEqual(self.texts(self.brief().overdue), ["quiet one"])
        self.assertEqual(self.brief(skip_silent=True).overdue, [])

    def test_when_labels(self):
        cases = {
            "2026-10-06": "overdue 2d",
            "2026-10-08T09:00": "overdue today",
            "2026-10-08T15:00": "today 15:00",
            "2026-10-08": "today",
            "2026-10-09T15:00": "tomorrow 15:00",
            "2026-10-16": "Fri 16 Oct",
        }
        for due, label in cases.items():
            with self.subTest(due=due):
                self.assertEqual(when_label({"due_at": due}, NOW), label)

    def test_banner_is_empty_when_nothing_needs_attention(self):
        self.add("no date")
        self.add("far away", "2026-12-01")
        self.assertEqual(format_banner(self.brief(horizon_days=2), NOW), "")

    def test_banner_content(self):
        self.add("Pay rent", "2026-10-06")
        self.add("Call Ali", "2026-10-08T15:00")
        self.add("Send invoice", "2026-10-09")
        banner = format_banner(self.brief(horizon_days=2), NOW)
        self.assertEqual(
            banner.splitlines(),
            [
                "📌 Notes: 1 overdue · 1 due today · 1 coming up",
                "  ! #1 Pay rent (overdue 2d)",
                "  • #2 Call Ali (today 15:00)",
                "  • #3 Send invoice (tomorrow)",
                "  /cos:notes-today for details",
            ],
        )

    def test_banner_is_capped(self):
        for n in range(7):
            self.add(f"late {n}", "2026-10-01")
        banner = format_banner(self.brief(horizon_days=2), NOW)
        self.assertEqual(len(banner.splitlines()), 1 + 4 + 1 + 1)
        self.assertIn("…and 3 more", banner)

    def test_today_view(self):
        self.assertIn("No open notes", format_today(self.brief(), NOW))
        self.add("Pay rent", "2026-10-06")
        self.add("Think about the database")
        text = format_today(self.brief(), NOW)
        self.assertIn("Overdue (1)", text)
        self.assertIn("#1 Pay rent (overdue 2d)", text)
        self.assertIn("No date (1)", text)
        self.assertIn("#2 Think about the database", text)

    def test_today_view_with_only_undated_notes(self):
        self.add("Think about the database")
        text = format_today(self.brief(), NOW)
        self.assertIn("Nothing is due in the next 7 days", text)
        self.assertIn("No date (1)", text)


if __name__ == "__main__":
    unittest.main()
