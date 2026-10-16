import unittest
from types import SimpleNamespace

from src.common import ROOT
from src.http import AccessError
from src.main import FixtureClient
from src.sources import era, lisa, usenix
from src.sources.base import collect


class SourceContracts(unittest.TestCase):
    def setUp(self):
        self.client = FixtureClient(ROOT / "tests/fixtures")

    def test_era_current_fellowship_remains_discoverable(self):
        result = collect(era, self.client, 3)
        self.assertIn("https://erafellowship.org/fellowship", [p.url for p in result.pages])
        self.assertTrue(any("Winter 2027" in p.html for p in result.pages))
        self.assertTrue(any("techgov.ai" in x for x in result.queued))

    def test_redirect_alias_does_not_duplicate_fellowship_page(self):
        result = collect(era, self.client, 3)
        urls = [page.url for page in result.pages]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(
            result.aliases.get("https://erafellowship.org/fellowship-1"),
            "https://erafellowship.org/fellowship",
        )
        self.assertFalse(result.failures)

    def test_lisa_is_not_usenix_lisa(self):
        result = collect(lisa, self.client, 3)
        self.assertEqual(len(result.pages), 1)
        self.assertIn("The London Initiative for Safe AI", result.pages[0].html)
        self.assertFalse(any("usenix" in x for x in result.leads))

    def test_usenix_discovers_conferences_and_cfp_links(self):
        result = collect(usenix, self.client, 3)
        self.assertEqual(len(result.pages), 3)
        self.assertIn("https://www.usenix.org/conference/sais27/call-for-papers", result.queued)
        self.assertTrue(usenix.event_path("/conference/srecon27americas/call-for-participation"))

    def test_fixture_miss_never_uses_network(self):
        with self.assertRaises(AccessError):
            self.client.fetch("https://unknown.example/")

    def test_denied_source_is_a_coverage_failure(self):
        class Denied:
            def fetch(self, url):
                raise AccessError("robots denied")

        result = collect(lisa, Denied())
        self.assertFalse(result.pages)
        self.assertEqual(result.failures[0]["reason"], "robots denied")

    def test_zero_page_budget_performs_no_fetches(self):
        result = collect(era, self.client, 0)
        self.assertFalse(result.pages)
        self.assertIn(era.seeds[0], result.queued)

    def test_historical_era_reference_is_not_lost(self):
        # Sanitized official mentor-page excerpt; historical metadata is not a new event.
        source = SimpleNamespace(
            name="era",
            seeds=["https://erafellowship.org/mentors"],
            hosts=era.hosts,
            partners=set(),
            event_path=era.event_path,
        )
        client = self.client
        result = collect(source, client, 1)
        self.assertIn("2025 Summer Mentors", result.pages[0].html)
        self.assertTrue(result.pages[0].fixture)


if __name__ == "__main__":
    unittest.main()
