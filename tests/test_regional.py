import importlib
import unittest
from datetime import date
from urllib.parse import urlsplit

from src.classify import classify
from src.extract import FIELDS, validate
from src.feasibility import deadline_date
from src.http import Page
from src.literal import extract_literals
from src.pages import parse


class RegionalTests(unittest.TestCase):
    def test_each_regional_adapter_has_official_seed_and_region(self):
        for name in (
            "europython",
            "pyconde",
            "pyconfi",
            "pyconjp",
            "pyconkr",
            "pyconus",
            "pydata",
            "iiba",
            "dama",
        ):
            with self.subTest(source=name):
                source = importlib.import_module("src.sources." + name)
                self.assertTrue(source.region)
                self.assertTrue(source.hosts)
                for url in source.seeds:
                    self.assertIn(urlsplit(url).hostname, source.hosts)
                self.assertTrue(callable(source.event_path))

    def test_each_source_has_a_saved_page_or_explicit_failure_fixture(self):
        from src.common import ROOT
        from src.main import FixtureClient
        from src.sources.base import collect

        client = FixtureClient(ROOT / "tests/fixtures")
        for name in (
            "europython",
            "pyconde",
            "pyconfi",
            "pyconjp",
            "pyconkr",
            "pyconus",
            "pydata",
            "iiba",
            "dama",
        ):
            batch = collect(importlib.import_module("src.sources." + name), client, 3)
            self.assertTrue(batch.pages or batch.failures)

    def test_literal_refresh_preserves_unknowns_and_free_virtual_evidence(self):
        page = Page(
            "https://go.iiba.org/Global-Business-Analysis-Day-2026",
            "<h1>Global Business Analysis Day 2026</h1><p>Free, fully virtual</p>",
            "unknown",
        )
        events = extract_literals(
            page, [{"name_pattern": "Global Business Analysis Day 2026"}], FIELDS
        )
        validate({"events": events}, page)
        self.assertEqual(events[0]["format"]["value"], "virtual")
        self.assertEqual(events[0]["start_date"]["value"], "unknown")
        record = {"fields": {k: events[0][k]["value"] for k in FIELDS}, "confidence": "verified"}
        self.assertEqual(classify(record)["primary_type"], "FREE")

    def test_catalog_cannot_transfer_another_event_grant(self):
        page = Page(
            "https://example.org/events/",
            "<h1>Example Conference 2027</h1><p>Other event: free registration and travel support.</p>",
            "unknown",
        )
        event = extract_literals(page, [{"name_pattern": "Example Conference 2027"}], FIELDS)[0]
        self.assertEqual(event["ticket_prices"]["value"], "unknown")
        self.assertEqual(event["grant_coverage"]["value"], "unknown")

    def test_japanese_and_korean_text_are_preserved(self):
        for phrase in ("2026年6月30日 AoE 募集は終了しました", "2026.8.15 컨퍼런스 마감"):
            text, _ = parse("<p>" + phrase + "</p>", "https://example.org/")
            self.assertEqual(text, phrase)

    def test_iso_deadline_has_no_invented_year(self):
        self.assertEqual(
            deadline_date("2026-12-27 (23:59 CET) – Application deadline."), date(2026, 12, 27)
        )


if __name__ == "__main__":
    unittest.main()
