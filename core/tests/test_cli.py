import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from notescos.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"NOTESCOS_HOME": tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(list(argv), out=out, now=datetime(2026, 10, 8, 10, 0))
        return code, out.getvalue(), err.getvalue()

    def test_add_list_done_flow(self):
        code, out, _ = self.run_cli("add", "Call", "Sara", "--due", "2026-10-09")
        self.assertEqual(code, 0)
        self.assertIn("#1 Call Sara (due 2026-10-09)", out)

        _, out, _ = self.run_cli("list")
        self.assertIn("[ ] #1 Call Sara", out)

        code, out, _ = self.run_cli("done", "1")
        self.assertEqual(code, 0)
        self.assertIn("[x] #1", out)

        _, out, _ = self.run_cli("list")
        self.assertEqual(out.strip(), "No notes.")
        _, out, _ = self.run_cli("list", "--all")
        self.assertIn("#1", out)

    def test_date_is_read_from_the_sentence(self):
        _, out, _ = self.run_cli("add", "Call Sara on 22 oct at 3pm")
        self.assertIn("(due 2026-10-22T15:00)", out)
        self.assertIn("Call Sara on 22 oct at 3pm", out)

    def test_guesses_are_shown_to_the_user(self):
        _, out, _ = self.run_cli("add", "Call Sara on 22 sep")
        self.assertIn("(due 2027-09-22)", out)
        self.assertIn("! 22 Sep has already passed", out)
        _, out, _ = self.run_cli("--json", "add", "Call Ali 22 sep")
        self.assertTrue(json.loads(out)["assumptions"])

    def test_due_flag_overrides_the_sentence(self):
        _, out, _ = self.run_cli("add", "Call Sara tomorrow", "--due", "2026-11-01")
        self.assertIn("(due 2026-11-01)", out)
        _, out, _ = self.run_cli("add", "Call Ali", "--due", "next friday")
        self.assertIn("(due 2026-10-16)", out)

    def test_note_without_a_date_has_none(self):
        _, out, _ = self.run_cli("add", "Think about the database")
        self.assertNotIn("due", out)

    def test_ambiguous_numeric_date_is_confirmed_in_the_reply(self):
        _, out, _ = self.run_cli("add", "Meet Ali 04/12")
        self.assertIn("(due 2026-12-04)", out)
        self.assertIn("! read 04/12 as day/month: Fri 04 Dec 2026", out)
        self.assertIn("Mon 12 Apr 2027", out)

    def test_date_order_setting(self):
        with mock.patch.dict(os.environ, {"NOTESCOS_DATE_ORDER": "mdy"}):
            _, out, _ = self.run_cli("add", "Meet Ali 04/12")
        self.assertIn("(due 2027-04-12)", out)
        with mock.patch.dict(os.environ, {"NOTESCOS_DATE_ORDER": "ymd"}):
            code, _, err = self.run_cli("add", "Meet Ali 04/12")
        self.assertEqual(code, 1)
        self.assertIn("NOTESCOS_DATE_ORDER", err)

    def test_json_output(self):
        _, out, _ = self.run_cli("--json", "add", "Ship it", "--tag", "release")
        self.assertEqual(json.loads(out)["tags"], ["release"])
        _, out, _ = self.run_cli("--json", "list")
        self.assertEqual([n["text"] for n in json.loads(out)], ["Ship it"])

    def test_errors_exit_nonzero_with_message(self):
        code, _, err = self.run_cli("done", "42")
        self.assertEqual(code, 1)
        self.assertIn("No note with id 42", err)
        code, _, err = self.run_cli("add", "x", "--due", "someday")
        self.assertEqual(code, 1)
        self.assertIn("YYYY-MM-DD", err)

    def test_money_types_not_yet_exposed(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            main(["add", "x", "--type", "money_owed"], out=io.StringIO())
