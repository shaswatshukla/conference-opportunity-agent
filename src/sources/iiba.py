"""Official iiba discovery; target region: Worldwide / Europe / US / virtual."""

import re

name = "iiba"
region = "Worldwide / Europe / US / virtual"
hosts = set(["www.iiba.org", "go.iiba.org", "germany.iiba.org", "finland.iiba.org"])
seeds = [
    "https://www.iiba.org/events/global-events-calendar/",
    "https://go.iiba.org/Global-Business-Analysis-Day-2026",
    "https://germany.iiba.org/Events",
]
partners = set()
rules = [{"name_pattern": "Global Business Analysis Day(?: 20[0-9]{2})?"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
