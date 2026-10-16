"""Official pyconus discovery; target region: US."""

import re

name = "pyconus"
region = "US"
hosts = set(["us.pycon.org"])
seeds = ["https://us.pycon.org/", "https://us.pycon.org/2027/"]
partners = set()
rules = [{"name_pattern": "PyCon US(?: 20[0-9]{2})?"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
