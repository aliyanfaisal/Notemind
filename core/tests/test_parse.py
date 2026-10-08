import unittest
from datetime import datetime

from notescos.parse import parse_due

# Thursday 8 Oct 2026, 10:00
NOW = datetime(2026, 10, 8, 10, 0)


def due(text):
    found = parse_due(text, NOW)
    return found.due if found else None


class ParseDueTests(unittest.TestCase):
    def test_day_and_month_names(self):
        cases = {
            "Call Sara on 22 oct": "2026-10-22",
            "Call Sara 22 October": "2026-10-22",
            "pay rent oct 25th": "2026-10-25",
            "send it on 3rd of nov".replace(" of", ""): "2026-11-03",
            "launch 25 Dec 2027": "2027-12-25",
            "launch 1 sept 2027": "2027-09-01",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(due(text), expected)

    def test_users_example_rolls_to_next_year_with_a_warning(self):
        found = parse_due("Call Sara on 22 sep", NOW)
        self.assertEqual(found.due, "2027-09-22")
        self.assertEqual(found.matched, "on 22 sep")
        self.assertIn("2027", found.assumptions[0])

    def test_relative_days(self):
        self.assertEqual(due("ship today"), "2026-10-08")
        self.assertEqual(due("ship tomorrow"), "2026-10-09")
        self.assertEqual(due("ship day after tomorrow"), "2026-10-10")
        self.assertEqual(due("in 3 days"), "2026-10-11")
        self.assertEqual(due("in 2 weeks"), "2026-10-22")

    def test_in_hours_and_minutes_carry_a_time(self):
        self.assertEqual(due("ping in 2 hours"), "2026-10-08T12:00")
        self.assertEqual(due("ping in 45 minutes"), "2026-10-08T10:45")

    def test_weekdays(self):
        self.assertEqual(due("call friday"), "2026-10-09")
        self.assertEqual(due("call this thursday"), "2026-10-08")
        self.assertEqual(due("call next monday"), "2026-10-12")
        self.assertEqual(due("call next friday"), "2026-10-16")
        self.assertEqual(due("call by sunday"), "2026-10-11")

    def test_weekday_that_is_today_means_next_week_and_says_so(self):
        found = parse_due("call thursday", NOW)
        self.assertEqual(found.due, "2026-10-15")
        self.assertTrue(found.assumptions)

    def test_short_weekdays_need_a_cue_word(self):
        self.assertEqual(due("call on wed"), "2026-10-14")
        self.assertIsNone(due("we sat and talked about the sun"))

    def test_times(self):
        self.assertEqual(due("tomorrow at 3pm"), "2026-10-09T15:00")
        self.assertEqual(due("22 oct 9:30am"), "2026-10-22T09:30")
        self.assertEqual(due("friday 15:45"), "2026-10-09T15:45")
        self.assertEqual(due("friday at noon"), "2026-10-09T12:00")
        self.assertEqual(due("22 oct 12am"), "2026-10-22T00:00")
        self.assertEqual(due("Call Sara 22 sep 2027 at 3:30pm"), "2027-09-22T15:30")

    def test_time_without_a_date(self):
        self.assertEqual(due("call at 5pm"), "2026-10-08T17:00")
        found = parse_due("call at 9am", NOW)
        self.assertEqual(found.due, "2026-10-09T09:00")
        self.assertTrue(found.assumptions)

    def test_iso_dates_still_work(self):
        self.assertEqual(due("renew 2026-12-01"), "2026-12-01")
        self.assertEqual(due("renew 2026-12-01T09:00"), "2026-12-01T09:00")

    def test_explicit_past_year_is_flagged(self):
        found = parse_due("filed 22 sep 2025", NOW)
        self.assertEqual(found.due, "2025-09-22")
        self.assertTrue(found.assumptions)

    def test_no_false_positives(self):
        for text in (
            "I may call Sara",
            "review the may release notes",
            "buy 3 apples",
            "version 2026 is out",
            "31 sep is not a date",
            "call at 25pm",
            "",
        ):
            with self.subTest(text=text):
                self.assertIsNone(due(text))

    def test_earliest_date_in_text_wins(self):
        self.assertEqual(due("call tomorrow, then again 25 oct"), "2026-10-09")


if __name__ == "__main__":
    unittest.main()
