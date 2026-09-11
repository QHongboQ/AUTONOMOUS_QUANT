"""Focused contract tests for the XNYS exchange_calendars adapter."""

from __future__ import annotations

import unittest

from aq_xnys_calendar import (
    date_to_session,
    is_session,
    next_session,
    previous_session,
    sessions_in_range,
)


ACCEPTED_IDENTITY_EFFECTIVE_SESSIONS = (
    "2013-09-30", "2017-12-05", "2019-01-02", "2017-11-15",
    "2019-07-01", "2019-11-05", "2019-12-10", "2022-01-10",
    "2022-05-10", "2024-02-01", "2024-03-25", "2019-10-18",
    "2020-03-03", "2022-02-17", "2023-07-10", "2022-06-09",
    "2011-12-16", "2013-05-01", "2017-04-03", "2018-07-10",
)


class XnysCalendarAdapterTests(unittest.TestCase):
    def test_weekday_session(self):
        self.assertTrue(is_session("2024-01-03"))

    def test_saturday_and_sunday_are_not_sessions(self):
        self.assertFalse(is_session("2024-01-06"))
        self.assertFalse(is_session("2024-01-07"))

    def test_xnys_holiday_is_not_session(self):
        self.assertFalse(is_session("2024-07-04"))

    def test_date_to_session_next_and_previous(self):
        self.assertEqual(date_to_session("2024-07-04", "next"), "2024-07-05")
        self.assertEqual(date_to_session("2024-07-04", "previous"), "2024-07-03")

    def test_previous_and_next_session(self):
        self.assertEqual(previous_session("2024-07-05"), "2024-07-03")
        self.assertEqual(next_session("2024-07-03"), "2024-07-05")

    def test_exact_inclusive_range(self):
        self.assertEqual(
            sessions_in_range("2024-07-01", "2024-07-05"),
            ("2024-07-01", "2024-07-02", "2024-07-03", "2024-07-05"),
        )

    def test_invalid_iso_fails_closed(self):
        for value in ("2024-7-05", "07/05/2024", "2024-02-30", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                is_session(value)

    def test_non_session_direction_none_fails_closed(self):
        with self.assertRaises(ValueError):
            date_to_session("2024-07-04", "none")

    def test_invalid_direction_fails_closed(self):
        with self.assertRaises(ValueError):
            date_to_session("2024-07-04", "nearest")  # type: ignore[arg-type]

    def test_range_requires_session_boundaries(self):
        with self.assertRaises(ValueError):
            sessions_in_range("2024-07-04", "2024-07-05")

    def test_all_accepted_identity_dates_are_xnys_sessions(self):
        self.assertEqual(len(ACCEPTED_IDENTITY_EFFECTIVE_SESSIONS), 20)
        for session in ACCEPTED_IDENTITY_EFFECTIVE_SESSIONS:
            with self.subTest(session=session):
                self.assertTrue(is_session(session))


if __name__ == "__main__":
    unittest.main()
