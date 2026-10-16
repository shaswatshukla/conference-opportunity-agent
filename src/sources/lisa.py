"""LISA is an organization. Do not label membership a free conference."""

name = "lisa"
hosts = {"www.safeai.org.uk", "safeai.org.uk"}
seeds = ["https://www.safeai.org.uk/"]
partners = {"www.arena.education", "arena.education", "www.arcadiaimpact.org"}


def event_path(path):
    return any(word in path.lower() for word in ("programme", "program", "event", "fellowship"))
