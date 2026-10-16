"""Official pyconde discovery; target region: Germany."""

import re

name = "pyconde"
region = "Germany"
hosts = set(["pycon.de", "www.pycon.de"])
seeds = ["https://pycon.de/", "https://pycon.de/financial-aid/"]
partners = set()
rules = [{"name_pattern": "PyCon DE(?: & PyData)? 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
