"""Official pyconjp discovery; target region: Japan."""

import re

name = "pyconjp"
region = "Japan"
hosts = set(["www.pycon.jp", "2026.pycon.jp"])
seeds = [
    "https://www.pycon.jp/",
    "https://2026.pycon.jp/en",
    "https://2026.pycon.jp/ja/travel-grants",
]
partners = set()
rules = [{"name_pattern": "PyCon JP 20[0-9]{2}"}]


def event_path(path):
    return bool(
        re.search(
            r"20[0-9]{2}|event|conference|grant|finaid|financial|volunteer|scholar|cfp", path, re.I
        )
    )
