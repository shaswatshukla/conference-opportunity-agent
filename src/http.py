"""Conservative public-only HTTP transport with cached robots and page bodies."""

import hashlib
import ipaddress
import json
import socket
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from .common import atomic_json, now

AGENT = "ConferenceOpportunityBot"
MAX_BYTES = 2_000_000


class AccessError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class Page:
    url: str
    html: str
    retrieved_at: str
    cached: bool = False
    fixture: bool = False


def safe_url(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise AccessError("Only public HTTPS URLs without credentials are allowed")
    if parts.port not in (None, 443):
        raise AccessError("Nonstandard port blocked")
    # Avoid persisting tracking, credential or token query strings.
    if parts.query:
        raise AccessError("Query URLs require a separately reviewed API adapter")
    try:
        addresses = socket.getaddrinfo(parts.hostname, 443)
    except OSError:
        raise AccessError("DNS resolution failed") from None
    if not addresses or any(not ipaddress.ip_address(addr[4][0]).is_global for addr in addresses):
        raise AccessError("Non-public destination blocked")
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", "", ""))


class Client:
    def __init__(self, cache, ttl_hours=24, interval=3, opener=None):
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_hours * 3600
        self.interval = interval
        self.last = {}
        self.robots = {}
        self.opener = opener or build_opener(NoRedirect())
        self.audit = []
        self.paused = set()
        self.backoff_file = self.cache / "backoff.json"
        self.backoff = (
            json.loads(self.backoff_file.read_text(encoding="utf-8"))
            if self.backoff_file.exists()
            else {}
        )

    def _key(self, url):
        return self.cache / (hashlib.sha256(url.encode()).hexdigest() + ".json")

    def _cached(self, url):
        path = self._key(url)
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            age = (
                datetime.now(UTC) - datetime.fromisoformat(value["retrieved_at"])
            ).total_seconds()
            if 0 <= age < self.ttl:
                return Page(**{**value, "cached": True})
        return None

    def _request(self, url, interval=None):
        host = urlsplit(url).netloc
        until = self.backoff.get(host)
        if host in self.paused or (until and datetime.fromisoformat(until) > datetime.now(UTC)):
            raise AccessError("Host rate-limited; request deferred")
        delay = max(self.interval, interval or 0) - (time.monotonic() - self.last.get(host, 0))
        if delay > 60:
            raise AccessError("Host pacing requires a later run")
        if delay > 0:
            time.sleep(delay)
        self.last[host] = time.monotonic()
        try:
            request = Request(
                url, headers={"User-Agent": AGENT + "/0.1 (public opportunity research)"}
            )
            with self.opener.open(request, timeout=20) as response:
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise AccessError("Response too large")
                if response.headers.get_content_type() not in (
                    "text/html",
                    "text/plain",
                    "application/xml",
                    "text/xml",
                ):
                    raise AccessError("Unsupported content type")
                return body.decode(
                    response.headers.get_content_charset() or "utf-8", errors="replace"
                )
        except HTTPError as error:
            if error.code in (429, 503):
                self.paused.add(host)
                retry = error.headers.get("Retry-After", "3600")
                try:
                    until = datetime.now(UTC) + timedelta(seconds=max(0, int(retry)))
                except ValueError:
                    try:
                        until = parsedate_to_datetime(retry)
                    except (TypeError, ValueError):
                        until = datetime.now(UTC) + timedelta(hours=1)
                self.backoff[host] = until.isoformat()
                atomic_json(self.backoff_file, self.backoff)
            raise
        except (URLError, OSError):
            raise AccessError("Network request failed") from None

    def _policy(self, url):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin in self.robots:
            return self.robots[origin]
        robots_url = origin + "/robots.txt"
        cached = self._cached(robots_url)
        if cached:
            text = cached.html
        else:
            try:
                text = self._request(robots_url)
            except HTTPError as error:
                if error.code == 404:
                    text = ""
                else:
                    raise AccessError(f"Robots unavailable: HTTP {error.code}") from None
            atomic_json(self._key(robots_url), asdict(Page(robots_url, text, now())))
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        self.robots[origin] = parser
        return parser

    def fetch(self, url, redirects=0):
        url = safe_url(url)
        policy = self._policy(url)
        if not policy.can_fetch(AGENT, url):
            raise AccessError("robots.txt disallows this page")
        cached = self._cached(url)
        if cached:
            self.audit.append({"url": url, "status": "cache", "retrieved_at": cached.retrieved_at})
            return cached
        interval = policy.crawl_delay(AGENT) or 0
        rate = policy.request_rate(AGENT)
        if rate and rate.requests:
            interval = max(interval, rate.seconds / rate.requests)
        try:
            html = self._request(url, interval)
        except HTTPError as error:
            if error.code in (301, 302, 303, 307, 308) and redirects < 4:
                return self.fetch(urljoin(url, error.headers.get("Location", "")), redirects + 1)
            raise AccessError(f"HTTP {error.code}; no retry or bypass attempted") from None
        page = Page(url, html, now())
        atomic_json(self._key(url), asdict(page))
        self.audit.append({"url": url, "status": "fetched", "retrieved_at": page.retrieved_at})
        return page
