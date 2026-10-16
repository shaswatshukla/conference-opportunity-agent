"""Bounded source contracts. Trust applies only to explicitly listed hosts."""

from dataclasses import dataclass, field
from urllib.parse import urlsplit

from ..http import AccessError
from ..pages import parse


@dataclass
class Batch:
    source: str
    pages: list = field(default_factory=list)
    leads: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    queued: list = field(default_factory=list)
    aliases: dict = field(default_factory=dict)


def collect(source, client, limit=4):
    result = Batch(source.name)
    visited = set()
    pending = list(source.seeds)
    while pending and len(visited) < limit:
        url = pending.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            page = client.fetch(url)
        except AccessError as error:
            result.failures.append({"url": url, "reason": str(error)})
            continue
        if page.url != url:
            result.aliases[url] = page.url
        if any(item.url == page.url for item in result.pages):
            continue
        visited.add(page.url)
        result.pages.append(page)
        _, links = parse(page.html, page.url)
        for link in links:
            parts = urlsplit(link)
            if parts.scheme != "https" or parts.query:
                continue
            if parts.hostname in source.hosts and source.event_path(parts.path):
                if link not in visited and link not in pending:
                    pending.append(link)
                result.leads.append(link)
            elif parts.hostname in source.partners:
                result.queued.append(link)
    result.queued = sorted(set(result.queued + pending))
    result.leads = sorted(set(result.leads))
    return result
