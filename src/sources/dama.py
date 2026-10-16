"""Official dama discovery; target region: Worldwide / Europe / US."""

import re

name = "dama"
region = "Worldwide / Europe / US"
hosts = set(["dama.org", "www.dama.org"])
seeds = [
    "https://dama.org/events-conferences/dama-global-conference-calendar/",
    "https://dama.org/events-conferences/upcoming-events-conferences-webinars-workshops/",
]
partners = set()
rules = [{"name_pattern": "DAMA Days 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
