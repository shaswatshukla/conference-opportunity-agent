"""Official pyconfi discovery; target region: Finland."""

import re

name = "pyconfi"
region = "Finland"
hosts = set(["fi.pycon.org", "2025.ploneconf.org"])
seeds = ["https://fi.pycon.org/"]
partners = set()
rules = [{"name_pattern": "PyCon (?:Finland|FI) 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
