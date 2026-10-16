"""Daily hosted run: no personal profile, logins, submissions or notifications."""

from .common import ROOT
from .main import discover


def main():
    snapshot, report = discover()
    (ROOT / "reports/latest.md").write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
    checked = sum(len(c["pages"]) for c in snapshot["coverage"])
    failed = sum(len(c["failures"]) for c in snapshot["coverage"])
    print(
        f"Checked {checked} official pages; {failed} source/page failures. See reports/latest.md."
    )
    if checked == 0:
        raise SystemExit("No official pages checked; coverage report preserved.")


if __name__ == "__main__":
    main()
