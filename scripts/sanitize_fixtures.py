"""Save small public regression fixtures from pages already lawfully cached."""
import hashlib
import html
import json
from src.common import ROOT, atomic_json
from src.pages import parse

base = ROOT / 'tests/fixtures'
manifest = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
for file in (ROOT / 'data/cache').glob('*.json'):
    page = json.loads(file.read_text(encoding='utf-8'))
    if 'url' not in page or page['url'].endswith('/robots.txt'):
        continue
    text, links = parse(page['html'], page['url'])
    clean = '<!doctype html><html><body><pre>' + html.escape(text) + '</pre>' + ''.join('<a href="' + html.escape(url, quote=True) + '"></a>' for url in links) + '</body></html>'
    name = hashlib.sha256(page['url'].encode()).hexdigest()[:16] + '.html'
    (base / name).write_text(clean, encoding='utf-8')
    manifest[page['url']] = {'file': name, 'retrieved_at': page['retrieved_at']}
    old_hash = hashlib.sha256(page['html'].encode()).hexdigest()
    envelope_path = ROOT / 'data/extractions' / (old_hash + '.json')
    if envelope_path.exists():
        envelope = json.loads(envelope_path.read_text(encoding='utf-8'))
        new_hash = hashlib.sha256(clean.encode()).hexdigest()
        envelope['page_sha256'] = new_hash
        atomic_json(base / 'extractions' / (new_hash + '.json'), envelope)
for alias, entry in list(manifest.items()):
    if 'canonical_url' in entry:
        canonical = entry['canonical_url']
        manifest[alias] = {**manifest[canonical], 'canonical_url': canonical}
snapshot = json.loads((ROOT / 'data/opportunities.json').read_text(encoding='utf-8'))
for source in snapshot['coverage']:
    for failed in source['failures']:
        if failed['url'] not in manifest:
            manifest[failed['url']] = {'error': failed['reason']}
atomic_json(base / 'manifest.json', manifest)
print('Saved', len(manifest), 'public page/failure fixture entries')
