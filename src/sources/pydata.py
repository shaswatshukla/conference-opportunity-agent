"""Official pydata discovery; target region: Worldwide / virtual."""

import re

name = "pydata"
region = "Worldwide / virtual"
hosts = set(["pydata.org", "amsterdam.pydata.org", "berlin.pydata.org"])
seeds = [
    "https://pydata.org/upcoming-events/",
    "https://pydata.org/global2026/",
    "https://amsterdam.pydata.org/conference",
]
partners = set()
rules = [{"name_pattern": "PyData (?:Global|Amsterdam|Berlin) 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
