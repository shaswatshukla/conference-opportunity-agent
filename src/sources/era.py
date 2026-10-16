"""ERA's official public fellowship pages; partners remain unverified leads."""

name = "era"
hosts = {"erafellowship.org", "www.erafellowship.org"}
seeds = ["https://erafellowship.org/"]
partners = {"www.techgov.ai", "techgov.ai", "www.securefrontier.ai", "www.aixbiosecurity.com"}


def event_path(path):
    return any(word in path.lower() for word in ("fellowship", "apply", "programme", "program"))


rules = [{"name_pattern": "ERA:AI Fellowship"}]
