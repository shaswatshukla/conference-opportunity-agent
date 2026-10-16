"""Prepare an explicit source-only GitHub upload. Never include personal files."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = {'README.md', 'AGENTS.md', 'ARCHITECTURE.md', 'SOURCES.md', 'flow.md', 'Makefile', 'requirements.txt', 'requirements-dev.txt', 'pyproject.toml', 'run.ps1', '.gitignore', '.env.example'}
PREFIXES = ('src/', 'config/', 'tests/', 'data/reference/', 'data/extractions/', '.github/workflows/', 'scripts/')
items = []
for file in sorted(ROOT.rglob('*')):
    if not file.is_file():
        continue
    relative = file.relative_to(ROOT).as_posix()
    if any(part in ('.deps', '.git', '__pycache__', '.ruff_cache', 'test-tmp') for part in file.parts):
        continue
    if relative not in TOP and relative != 'data/profile.example.yaml' and relative != 'reports/latest.md' and not relative.startswith(PREFIXES):
        continue
    if file.suffix in ('.pyc', '.pyd', '.exe'):
        continue
    items.append({'path': relative, 'mode': '100644', 'type': 'blob', 'content': file.read_text(encoding='utf-8-sig')})
assert not any(x['path'] in ('data/profile.yaml', 'data/answers.yaml', '.env') for x in items)
index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
print(json.dumps({"items": items[index * 10:(index + 1) * 10], "chunks": (len(items) + 9) // 10, "files": len(items)}, ensure_ascii=True))
