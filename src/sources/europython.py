"""Official europython discovery; target region: Europe."""

import re

name = "europython"
region = "Europe"
hosts = set(["europython.eu", "ep2026.europython.eu"])
seeds = ["https://europython.eu/", "https://ep2026.europython.eu/finaid/"]
partners = set()
rules = [{"name_pattern": "EuroPython 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
