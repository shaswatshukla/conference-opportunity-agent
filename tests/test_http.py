import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from src.common import ROOT, now
from src.http import AccessError, Client, Page, safe_url
from src.pages import parse


class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "data/test-tmp").mkdir(parents=True, exist_ok=True)

    def test_private_addresses_and_credential_urls_rejected(self):
        with patch("src.http.socket.getaddrinfo", return_value=[(0, 0, 0, "", ("127.0.0.1", 443))]):
            with self.assertRaises(AccessError):
                safe_url("https://internal.example/")
        for url in (
            "http://example.com/",
            "https://user:secret@example.com/",
            "https://example.com/?token=secret",
        ):
            with self.assertRaises(AccessError):
                safe_url(url)

    def test_dns_failure_is_clean_failure(self):
        with patch("src.http.socket.getaddrinfo", side_effect=OSError()):
            with self.assertRaisesRegex(AccessError, "DNS"):
                safe_url("https://example.com/")

    def test_denied_robots_never_fetches_page(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            client = Client(Path(directory), interval=0)
            with (
                patch("src.http.safe_url", side_effect=lambda x: x),
                patch.object(
                    client, "_request", return_value="User-agent: *\nDisallow: /"
                ) as request,
            ):
                with self.assertRaisesRegex(AccessError, "disallows"):
                    client.fetch("https://example.com/")
                self.assertEqual(request.call_count, 1)

    def test_robots_403_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            client = Client(Path(directory), interval=0)
            error = HTTPError("https://example.com/robots.txt", 403, "Forbidden", {}, None)
            with (
                patch("src.http.safe_url", side_effect=lambda x: x),
                patch.object(client, "_request", side_effect=error),
            ):
                with self.assertRaisesRegex(AccessError, "Robots unavailable"):
                    client.fetch("https://example.com/")

    def test_cache_hit_keeps_original_retrieval_time(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            client = Client(Path(directory), interval=0)
            page = Page("https://example.com/", "<p>Public</p>", now())
            client._key(page.url).write_text(json.dumps(page.__dict__))
            with (
                patch("src.http.safe_url", side_effect=lambda x: x),
                patch.object(client, "_request", return_value="User-agent: *\nAllow: /") as request,
            ):
                result = client.fetch(page.url)
                self.assertTrue(result.cached)
                self.assertEqual(result.retrieved_at, page.retrieved_at)
                self.assertEqual(request.call_count, 1)  # robots only

    def test_retry_after_blocks_host_and_persists_across_clients(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            client = Client(Path(directory), interval=0)
            error = HTTPError(
                "https://example.com/", 429, "Rate limited", {"Retry-After": "300"}, None
            )
            with patch.object(client.opener, "open", side_effect=error):
                with self.assertRaises(HTTPError):
                    client._request("https://example.com/")
            again = Client(Path(directory), interval=0)
            with patch.object(again.opener, "open") as request:
                with self.assertRaisesRegex(AccessError, "rate-limited"):
                    again._request("https://example.com/next")
                request.assert_not_called()

    def test_scripts_cannot_supply_evidence_or_links(self):
        text, links = parse(
            '<p>Visible fact.</p><script>Free flights<a href="https://bad.example/">x</a></script>',
            "https://example.com/",
        )
        self.assertEqual(text, "Visible fact.")
        self.assertEqual(links, [])


if __name__ == "__main__":
    unittest.main()
