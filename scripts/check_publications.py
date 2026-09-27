#!/usr/bin/env python3
"""Release checks for report links and consistency across all render paths."""
import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
PUB = DOCS / 'research'


def decode_payload(raw):
    values = json.loads(raw)
    def read(ref):
        if ref < 0:
            return None
        v = values[ref]
        if isinstance(v, dict):
            return {k: read(i) for k, i in v.items()}
        if isinstance(v, list):
            if v and isinstance(v[0], str):
                return read(v[1]) if len(v) == 2 else []
            return [read(i) for i in v]
        return v
    return read(0)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links, self.keys, self.h1 = [], [], 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag == 'section' and a.get('data-key', '').startswith('publications-'):
            self.keys.append(a['data-key'])
        if tag == 'h1':
            self.h1 += 1


def main():
    data = json.loads((PUB / 'publications.json').read_text())
    entries = data['reports'] + [data['evidence']]
    client = json.loads((DOCS / '_nuxt/replica-data.js').read_text().removeprefix('export default ').rstrip(';\n'))
    expected = client['sanity-research']['pageModules']
    source = (PUB / 'index.html').read_text()
    embedded = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', source)[1]
    for raw in [embedded, (PUB / '_payload.json').read_text()]:
        assert decode_payload(raw)['data']['sanity-research']['pageModules'] == expected
    page = Page(source)
    assert page.keys == [m['_key'] for m in expected if m['_key'].startswith('publications-')]
    assert len(page.keys) == len(set(page.keys)) == len(entries) + 1
    for r in entries:
        url = 'https://sushxnthd.github.io/kernellum/research/' + r['slug'] + '/'
        assert page.links.count(url) == 1, f'Missing or duplicate report link: {url}'
        detail = Page((PUB / r['slug'] / 'index.html').read_text())
        assert detail.h1 == 1
        pdf = '/kernellum/research/files/' + r['pdf']
        assert detail.links.count(pdf) == 2, 'Read and download links required'
        for link in detail.links:
            u = urlparse(link)
            if u.path.startswith('/kernellum/') and (not u.netloc or u.netloc == 'sushxnthd.github.io'):
                target = DOCS / u.path.removeprefix('/kernellum/')
                if u.path.endswith('/'):
                    target /= 'index.html'
                assert target.is_file(), f'Broken local link: {link}'
    files = [p for p in PUB.rglob('*') if p.is_file()] + [DOCS / '_nuxt/replica-data.js']
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in files}
    subprocess.run(['python3', str(ROOT / 'scripts/build_publications.py')], check=True)
    assert all(hashlib.sha256(p.read_bytes()).digest() == h for p, h in before.items()), 'Build not idempotent'
    print('PASS: all render paths agree; unique report entries; detail/PDF links resolve; repeat build unchanged.')


if __name__ == '__main__':
    main()
