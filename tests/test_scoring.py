import copy
import unittest
from datetime import date
from decimal import Decimal

from src.classify import classify, money
from src.common import ROOT, config
from src.dedupe import dedupe
from src.extract import extract
from src.feasibility import FX, deadline_date, evaluate, reference
from src.main import FixtureClient
from src.score import score
from src.sources import era
from src.verify import verify


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 16)
        self.fx = FX(reference(ROOT, "fx.json"), self.today)
        client = FixtureClient(ROOT / "tests/fixtures")
        page = client.fetch("https://erafellowship.org/fellowship")
        events, mode = extract(page, ROOT / "tests/fixtures/extractions")
        detail = verify(events[0], era, client, page, mode)
        home = client.fetch("https://erafellowship.org/")
        home_events, home_mode = extract(home, ROOT / "tests/fixtures/extractions")
        self.record = dedupe([verify(home_events[0], era, client, home, home_mode), detail])[0]
        # Classification tests concern source facts; fixture verification behavior is tested separately.
        self.record["confidence"] = "verified"
        self.record["classification"] = classify(self.record, 100, self.fx.convert)
        self.record["feasibility"] = evaluate(
            self.record, config("estimates.yaml"), self.fx, reference(ROOT, "visa.json"), self.today
        )

    def test_paid_fellowship_is_grant_not_free_ticket(self):
        self.assertEqual(self.record["classification"]["primary_type"], "SCHOLARSHIP/GRANT")
        self.assertEqual(self.record["fields"]["programme_kind"], "fellowship")
        self.assertNotIn("FREE", self.record["classification"]["secondary_types"])

    def test_conditional_stipend_is_not_deducted_from_cost(self):
        f = self.record["feasibility"]
        self.assertEqual(f["published_support_amount"]["amount"], "10000")
        self.assertGreater(f["estimated_travel_stay_inr"], 0)
        self.assertEqual(f["total_cost_after_grant_inr"], "unknown")
        self.assertEqual(f["visa"]["route"], "unknown")
        self.assertEqual(f["visa"]["lead_days"], "unknown")
        self.assertFalse(f["actionable"])

    def test_fx_uses_correct_cross_rate_and_expires(self):
        expected = (Decimal("10000") / Decimal("0.84385") * Decimal("106.864")).quantize(
            Decimal("0.01")
        )
        self.assertEqual(self.fx.convert("10000", "GBP", "INR"), str(expected))
        stale = FX(reference(ROOT, "fx.json"), date(2026, 11, 1))
        self.assertIsNone(stale.convert(100, "GBP", "INR"))

    def test_currency_and_deadline_unknowns_are_not_guessed(self):
        self.assertIsNone(money("$100"))
        self.assertIsNone(deadline_date("November 19"))
        self.assertEqual(deadline_date("Talk proposals due November 19, 2026"), date(2026, 11, 19))
        self.assertEqual(self.record["feasibility"]["deadline"]["timezone"], "unknown")

    def test_threshold_is_strictly_under_100_and_negation_is_not_free(self):
        r = copy.deepcopy(self.record)
        r["fields"].update(grant_coverage="unknown", deadlines="unknown", ticket_prices="USD 100")
        self.assertEqual(classify(r, 100, self.fx.convert)["primary_type"], "unknown")
        r["fields"]["ticket_prices"] = "USD 99"
        self.assertEqual(classify(r, 100, self.fx.convert)["primary_type"], "LOW_COST")
        r["fields"]["ticket_prices"] = "Registration is not free registration"
        self.assertEqual(classify(r, 100, self.fx.convert)["primary_type"], "unknown")

    def test_closed_cycle_and_missing_eligibility_earn_no_points(self):
        result = score(
            self.record,
            config("scoring_weights.yaml"),
            config("interests.yaml")["interests"],
            {"review_status": "awaiting_user_review"},
        )
        self.assertEqual(result["bucket"], "closed")
        self.assertEqual(result["components"]["deadline_feasibility"]["points"], 0)
        self.assertEqual(result["components"]["eligibility_certainty"]["points"], 0)
        self.assertEqual(result["components"]["net_cost"]["points"], 0)
        self.assertEqual(result["components"]["networking_hiring"]["points"], 0)
        self.assertGreater(result["total"], 0)

    def test_invalid_weights_are_rejected(self):
        weights = config("scoring_weights.yaml")
        weights["relevance"] = 0.9
        with self.assertRaises(ValueError):
            score(self.record, weights, [], {})

    def test_unverified_record_cannot_gain_positive_score(self):
        self.record["confidence"] = "unverified"
        result = score(
            self.record, config("scoring_weights.yaml"), config("interests.yaml")["interests"], {}
        )
        self.assertEqual(result["total"], 0)

    def test_free_virtual_scenario_does_not_require_travel_or_visa(self):
        r = copy.deepcopy(self.record)
        r["fields"].update(
            format="virtual",
            ticket_prices="free registration",
            grant_coverage="unknown",
            application_status="open",
            deadlines="Applications due November 19, 2026",
        )
        r["classification"] = classify(r, 100, self.fx.convert)
        f = evaluate(r, config("estimates.yaml"), self.fx, reference(ROOT, "visa.json"), self.today)
        self.assertEqual(f["estimated_travel_stay_inr"], 0)
        self.assertEqual(f["total_cost_after_grant_inr"], 0)
        self.assertEqual(f["visa"]["lead_days"], 0)
        self.assertTrue(f["actionable"])


if __name__ == "__main__":
    unittest.main()
