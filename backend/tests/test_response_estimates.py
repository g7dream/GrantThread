"""Deterministic estimate examples and authority checks; no live funder claims."""
import copy
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grantthread.api import dispatch
from grantthread.errors import DomainError
from grantthread.repository import SQLiteRepository
from grantthread.response_estimates import SIMULATED_HISTORY, estimate_response_time
from grantthread.seed import IDENTITIES, seed_all
from grantthread.service import Service
from grantthread.storage import LocalStorage


TODAY = date(2026, 9, 6)


class EstimateMath(unittest.TestCase):
    def estimate(self, submitted, history=None):
        return estimate_response_time(SIMULATED_HISTORY["northstar"] if history is None else history, submitted, TODAY)

    def test_seven_day_wait_has_concrete_remaining_window(self):
        result = self.estimate("2026-08-30")
        self.assertEqual(result["elapsedDays"], 7)
        self.assertEqual(result["remainingDays"], {"low": 5, "typical": 11, "high": 15})
        self.assertEqual(result["expectedDates"], {"earliest": "2026-09-11", "typical": "2026-09-17", "latest": "2026-09-21"})
        self.assertEqual(result["typicalTotalDays"], 18)
        self.assertEqual((result["sampleCount"], result["comparableSampleCount"]), (12, 12))
        self.assertTrue(result["simulated"])

    def test_long_wait_uses_still_comparable_reviews(self):
        result = self.estimate("2026-08-14")  # 23 days waited, beyond the unconditional median.
        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["comparableSampleCount"], 3)
        self.assertEqual(result["remainingDays"], {"low": 2, "typical": 5, "high": 12})

    def test_small_tail_does_not_make_a_countdown(self):
        result = self.estimate("2026-08-12")  # 25 days, only two longer completed examples.
        self.assertEqual(result["status"], "insufficient_history")
        self.assertEqual(result["comparableSampleCount"], 2)
        self.assertIsNone(result["remainingDays"])
        self.assertIsNone(result["expectedDates"])

    def test_at_or_beyond_longest_wait_never_promises_today(self):
        for submitted in ("2026-08-02", "2025-01-01"):
            with self.subTest(submitted=submitted):
                result = self.estimate(submitted)
                self.assertEqual(result["status"], "beyond_history")
                self.assertIsNone(result["remainingDays"])
                self.assertIsNone(result["expectedDates"])

    def test_missing_history_has_no_invented_fallback(self):
        result = self.estimate("2026-09-06", [])
        self.assertEqual(result["status"], "insufficient_history")
        self.assertEqual(result["sampleCount"], 0)
        self.assertIsNone(result["typicalTotalDays"])
        self.assertIsNone(result["historicalRangeDays"])

    def test_dates_are_strict_and_future_dates_rejected(self):
        for value in (None, [], 1, "20260901", "2026-9-01", "2026-02-30", "2026-09-06T00:00:00Z", "2026-09-07"):
            with self.subTest(value=value), self.assertRaises(DomainError):
                self.estimate(value)

    def test_calendar_days_include_month_boundaries_and_leap_day(self):
        result = estimate_response_time([5, 10, 15, 20], "2024-02-28", date(2024, 3, 1))
        self.assertEqual(result["elapsedDays"], 2)
        self.assertEqual(result["expectedDates"]["earliest"], "2024-03-04")


class EstimateScope(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"GRANTTHREAD_MODE": "local", "GRANTTHREAD_DATA_DIR": self.temp.name})
        self.env.start()
        self.repository = SQLiteRepository(Path(self.temp.name) / "test.sqlite3")
        self.storage = LocalStorage(self.temp.name)
        seed_all(self.repository, self.storage)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def request(self, identity="brightpath", body=None):
        return dispatch("POST", "/api/response-estimates", body or {"grantId": "digital-belonging", "submittedDate": "2026-08-30"},
                        IDENTITIES[identity], self.repository, self.storage)

    def test_route_scopes_funder_history_without_mutating_records(self):
        before = copy.deepcopy(self.repository.read("brightpath"))
        with patch("grantthread.service.estimate_response_time", side_effect=lambda history, submitted: estimate_response_time(history, submitted, TODAY)):
            result = self.request()
            riverbend = self.request(body={"grantId": "community-makers", "submittedDate": "2026-08-30"})
        self.assertEqual(result["funderName"], "Northstar Foundation")
        self.assertEqual(result["grantId"], "digital-belonging")
        self.assertNotEqual(result["historyDays"], riverbend["historyDays"])
        self.assertEqual(before, self.repository.read("brightpath"))

    def test_funder_and_other_grantee_cannot_query_a_grant(self):
        for identity, code in (("northstar", "forbidden"), ("harbour", "not_found")):
            with self.subTest(identity=identity), self.assertRaises(DomainError) as caught:
                self.request(identity)
            self.assertEqual(caught.exception.code, code)

    def test_unconfigured_funder_does_not_inherit_another_funders_history(self):
        self.repository.mutate("brightpath", lambda data: data["grants"]["digital-belonging"].update(funderOrgId="new-funder"))
        result = self.request()
        self.assertEqual(result["sampleCount"], 0)
        self.assertIsNone(result["remainingDays"])

    def test_malformed_grant_and_body_are_domain_errors(self):
        service = Service(IDENTITIES["brightpath"], self.repository, self.storage)
        for body in (None, [], {}, {"grantId": []}, {"grantId": "unknown", "submittedDate": "2026-08-30"}):
            with self.subTest(body=body), self.assertRaises(DomainError):
                service.response_estimate(body)


if __name__ == "__main__":
    unittest.main()
