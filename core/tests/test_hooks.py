import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from notescos.cli import main
from notescos.hooks import session_start
from notescos.store import NoteStore

NOW = datetime(2026, 10, 8, 10, 0)


class SessionStartTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)

    def add(self, text, due):
        with NoteStore(self.home / "notes.db") as store:
            store.add(text, due=due)

    def test_first_run_shows_welcome_once(self):
        first = session_start("{}", NOW, self.home)
        self.assertIn("Notes Chief of Staff is ready", first["systemMessage"])
        self.assertIsNone(session_start("{}", NOW, self.home))

    def test_banner_goes_to_user_and_to_claude(self):
        (self.home / "welcomed").write_text("x")
        self.add("Pay rent", "2026-10-06")
        result = session_start('{"source": "startup"}', NOW, self.home)
        self.assertIn("1 overdue", result["systemMessage"])
        self.assertIn("#1 Pay rent", result["systemMessage"])
        context = result["hookSpecificOutput"]
        self.assertEqual(context["hookEventName"], "SessionStart")
        self.assertIn("Pay rent", context["additionalContext"])
        json.dumps(result)  # must be serialisable

    def test_nothing_to_say_means_no_output(self):
        (self.home / "welcomed").write_text("x")
        self.add("far away", "2027-01-01")
        self.assertIsNone(session_start("{}", NOW, self.home))

    def test_compact_does_not_repeat_the_banner(self):
        self.add("Pay rent", "2026-10-06")
        self.assertIsNone(session_start('{"source": "compact"}', NOW, self.home))
        self.assertFalse((self.home / "welcomed").exists())

    def test_resume_and_clear_do_show_it(self):
        (self.home / "welcomed").write_text("x")
        self.add("Pay rent", "2026-10-06")
        for source in ("resume", "clear"):
            with self.subTest(source=source):
                self.assertIsNotNone(session_start(json.dumps({"source": source}), NOW, self.home))

    def test_garbage_stdin_is_tolerated(self):
        self.add("Pay rent", "2026-10-06")
        self.assertIsNotNone(session_start("not json", NOW, self.home))


class HookCommandTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        patcher = mock.patch.dict(os.environ, {"NOTESCOS_HOME": tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_hook(self, stdin_text):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin_text)):
            code = main(["hook", "session-start"], out=out, now=NOW)
        return code, out.getvalue()

    def test_prints_valid_json(self):
        code, out = self.run_hook('{"source": "startup"}')
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_broken_database_never_breaks_the_session(self):
        (self.home / "notes.db").write_text("this is not a database")
        code, out = self.run_hook("{}")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertIn("Traceback", (self.home / "log").read_text())


class StdinAddTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"NOTESCOS_HOME": tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_add_reads_text_from_stdin(self):
        out = io.StringIO()
        text = "Call Sara's \"office\" $(date) `ls`; on 22 oct\n"
        with mock.patch("sys.stdin", io.StringIO(text)), contextlib.redirect_stderr(io.StringIO()):
            code = main(["--json", "add", "-"], out=out, now=NOW)
        note = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(note["text"], "Call Sara's \"office\" $(date) `ls`; on 22 oct")
        self.assertEqual(note["due_at"], "2026-10-22")

    def test_today_command(self):
        with NoteStore() as store:
            store.add("Pay rent", due="2026-10-06")
        out = io.StringIO()
        main(["today"], out=out, now=NOW)
        self.assertIn("Overdue (1)", out.getvalue())
        out = io.StringIO()
        main(["--json", "today"], out=out, now=NOW)
        self.assertEqual(len(json.loads(out.getvalue())["overdue"]), 1)


if __name__ == "__main__":
    unittest.main()
