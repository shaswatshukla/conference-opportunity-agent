"""Official pyconkr discovery; target region: South Korea."""

import re

name = "pyconkr"
region = "South Korea"
hosts = set(["pycon.kr", "2026.pycon.kr"])
seeds = ["https://pycon.kr/", "https://2026.pycon.kr/"]
partners = set()
rules = [{"name_pattern": "PyCon Korea 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
