"""USENIX calendar and bounded official event-page expansion."""

import re

name = "usenix"
hosts = {"www.usenix.org", "usenix.org"}
seeds = [
    "https://www.usenix.org/conferences",
    "https://www.usenix.org/conference/srecon27americas",
    "https://www.usenix.org/conference/sais27",
]
partners = set()


def event_path(path):
    return bool(
        re.search(
            r"/conference/[^/]+(?:/(?:cfp|call-for-papers|call-for-participation|grants|registration|attend))?/?$",
            path,
        )
    )


rules = [
    {"name_pattern": "USENIX Conference on Secure Agentic-AI Systems"},
    {"name_pattern": r"SREcon[0-9]{2} Americas"},
]
