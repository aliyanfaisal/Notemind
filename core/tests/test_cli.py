import contextlib
import io
import json
import os
import tempfile
import unittest
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
            code = main(list(argv), out=out)
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
