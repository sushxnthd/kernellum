#!/usr/bin/env python3
"""Build publications using existing Nuxt textIntro modules, never DOM injection.

Run from any directory: python3 scripts/build_publications.py
The committed static HTML, Nuxt payload and client data must agree.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
PUB = DOCS / 'research'
BASE = 'https://sushxnthd.github.io/kernellum'
PREFIX = 'publications-'
esc = html.escape


def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def block(key, text, style='normal'):
    return {'_key': key, '_type': 'toolbar', 'style': style, 'markDefs': [],
            'children': [{'_key': key + '-span', '_type': 'span', 'marks': [], 'text': text}]}


def button(key, text, url):
    # Absolute URLs intentionally leave the Nuxt router: publication detail pages
    # are static documents, not routes in the original application bundle.
    return {'_key': key, '_type': 'button', 'markDefs': None, 'text': text,
            'link': {'type': 'url', 'url': url, 'newTab': False}}


def intro(key, label, content):
    return {'_key': PREFIX + key, '_type': 'textIntro', 'highlightText': False,
            'label': label, 'content': content}


def replace_modules(modules, publications):
    clean = [m for m in modules if not m['_key'].startswith(PREFIX)]
    position = next(i for i, m in enumerate(clean) if m['_key'] == '80bdb76a9b67')
    return clean[:position] + publications + clean[position:]


def update_payload(raw, modules):
    """Append new devalue nodes; preserve Nuxt's existing refs and tagged values."""
    values = json.loads(raw)
    def add(v):
        index = len(values)
        values.append(None)
        if isinstance(v, dict):
            values[index] = {k: add(x) for k, x in v.items()}
        elif isinstance(v, list):
            values[index] = [add(x) for x in v]
        else:
            values[index] = v
        return index
    page = next(v for v in values if isinstance(v, dict) and
                'pageModules' in v and values[v.get('title', 0)] == 'Research')
    # Reuse the pageModules root so references remain valid. Rebuild from the
    # canonical client data, removing stale research copy in legacy payloads.
    index = page['pageModules']
    values[index] = [add(m) for m in modules]
    # Compact reachable nodes so repeated builds are byte-identical.
    compact, seen = [], {}
    def copy_ref(ref):
        if ref < 0:
            return ref
        if ref in seen:
            return seen[ref]
        index = len(compact)
        seen[ref] = index
        compact.append(None)
        value = values[ref]
        if isinstance(value, dict):
            compact[index] = {k: copy_ref(v) for k, v in value.items()}
        elif isinstance(value, list):
            compact[index] = [v if isinstance(v, str) else copy_ref(v) for v in value]
        else:
            compact[index] = value
        return index
    copy_ref(0)
    return dump(compact)


def render_intro(module, button_template):
    parts = []
    for b in module['content']:
        if b['_type'] == 'button':
            value = re.sub(r'href="[^"]*"', 'href="' + esc(b['link']['url']) + '"', button_template)
            value = re.sub(r'_key="[^"]*"', '_key="' + b['_key'] + '"', value)
            value = re.sub(r'<span class="text">.*?</span>', '<span class="text">' + esc(b['text']) + '</span>', value)
            value = re.sub(r' target="[^"]*"', '', value).replace('<a ', '<a target="_self" ', 1)
            value = value.replace(' rel="noopener noreferrer"', '')
            parts.append(value)
        else:
            tag = 'p' if b['style'] in ('normal', 'label') else b['style']
            cls = ' class="text-label"' if b['style'] == 'label' else ''
            parts.append(f'<{tag}{cls}>{esc(b["children"][0]["text"])}</{tag}>')
    return (f'<section class="text-intro" data-key="{module["_key"]}" data-v-82229777>'
            '<div class="left" data-v-82229777><p class="text-label" data-v-82229777>'
            + esc(module['label']) + '</p></div><div class="block-text default" data-v-82229777 data-v-b6617ed5>'
            '<div class="col" data-v-b6617ed5><!--[-->' + ''.join(parts) + '<!--]--></div></div></section>')


def report_page(r):
    pdf = f'/kernellum/research/files/{r["pdf"]}'
    size = (PUB / 'files' / r['pdf']).stat().st_size / 1_000_000
    meta = ''.join(f'<div>{a}<strong>{esc(b)}</strong></div>' for a, b in [
        ('Report ID', r['id']), ('Publication', r['dateLabel']),
        ('Author', 'Sushanth Dasari'), ('Research lane', r['topic'])])
    metrics = ''.join(f'<div class="pub-metric"><strong>{esc(x["value"])}</strong><span>{esc(x["label"])}</span></div>' for x in r['results'])
    links = ''.join(f'<a class="pub-link" href="{esc(x["url"])}" target="_blank" rel="noopener noreferrer"><strong>{esc(x["title"])}</strong><span>Open ↗</span></a>' for x in r['artifacts'])
    citation = f'Dasari, S. (2026). {r["title"]}. Kernellum Research, {r["shortId"]}.'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(r['shortId'])}: {esc(r['title'])} • Kernellum Research</title>
<meta name="description" content="{esc(r['subtitle'])}"><link rel="canonical" href="{BASE}/research/{r['slug']}/">
<meta name="citation_title" content="{esc(r['title'])}"><meta name="citation_author" content="Sushanth Dasari">
<meta name="citation_publication_date" content="{r['date']}"><meta name="citation_pdf_url" content="https://sushxnthd.github.io{pdf}">
<link rel="icon" type="image/svg+xml" href="/kernellum/favi/kernellum.svg"><link rel="stylesheet" href="/kernellum/research/report-page.css"></head>
<body><a class="pub-skip" href="#report">Skip to report</a><nav class="pub-nav" aria-label="Research navigation"><a class="pub-brand" href="/kernellum/">Kernellum Research</a><a class="pub-back" href="/kernellum/research/">← All research</a></nav>
<main id="report" class="pub-wrap"><div class="pub-meta">{meta}</div>
<section class="pub-hero"><div><span class="pub-label">{esc(r['type'])} / {esc(r['shortId'])}</span></div><div><h1>{esc(r['title'])}</h1><p>{esc(r['subtitle'])}</p>
<div class="pub-downloads"><a class="pub-action primary" href="{pdf}" target="_blank" rel="noopener">Read PDF ↗</a><a class="pub-action" href="{pdf}" download="{r['pdf']}">Download PDF ↓</a><span>PDF · {size:.2f} MB</span></div></div></section>
<section class="pub-section"><div class="pub-section-grid"><div><span class="pub-label">Research record</span><h2>What this report establishes.</h2></div><div class="pub-copy">{r['abstract']}</div></div></section>
<section class="pub-section"><div class="pub-section-grid"><div><span class="pub-label">Selected evidence</span><h2>Measured results.</h2></div><div class="pub-metrics">{metrics}</div></div></section>
<section class="pub-section"><div class="pub-section-grid"><div><span class="pub-label">Reproducibility</span><h2>Primary artifacts.</h2></div><div class="pub-links">{links}</div></div></section>
<section class="pub-section"><div class="pub-section-grid"><div><span class="pub-label">Citation</span><h2>Reference this report.</h2></div><p class="pub-copy">{esc(citation)}</p></div></section>
<footer class="pub-footer"><span>{esc(r['id'])} • Kernellum Research</span><a href="/kernellum/research/">All publications ↗</a></footer></main></body></html>'''


def main():
    data = json.loads((PUB / 'publications.json').read_text())
    reports = sorted(data['reports'], key=lambda r: (r['date'], r['shortId']), reverse=True)
    entries = reports + [data['evidence']]
    assert len({r['slug'] for r in entries}) == len(entries), 'Duplicate publication slug'
    for r in entries:
        assert re.fullmatch(r'[a-z0-9-]+', r['slug']), 'Invalid slug'
        assert (PUB / 'files' / r['pdf']).read_bytes().startswith(b'%PDF-'), 'Missing PDF'
        for artifact in r['artifacts']:
            path = artifact['url'].split('/blob/main/')[-1]
            assert (ROOT / path).is_file(), f'Missing repository artifact: {path}'
    publications = [intro('heading', 'Research publications', [
        block('publication-title', 'Technical reports', 'h2'),
        block('publication-summary', 'Methods, measured results, and the artifacts behind them. Read the full reports or follow the evidence back to the repository.')])]
    for r in entries:
        key = r['slug']
        publications.append(intro(key, 'Evidence & reproducibility' if key == 'evidence' else r['shortId'], [
            block(key+'-date', r['dateLabel']+' / '+r['type'], 'label'),
            block(key+'-title', r['title'], 'h3'),
            block(key+'-summary', r['summary']),
            button(key+'-read', 'Read '+('evidence dossier' if key == 'evidence' else r['shortId']), BASE+'/research/'+key+'/')]))
    client_path = DOCS / '_nuxt/replica-data.js'
    client = json.loads(client_path.read_text().removeprefix('export default ').rstrip(';\n'))
    modules = replace_modules(client['sanity-research']['pageModules'], publications)
    client['sanity-research']['pageModules'] = modules
    client_path.write_text('export default '+dump(client)+';')
    page_path = PUB / 'index.html'
    page = page_path.read_text()
    page = re.sub(r'<section class="text-intro" data-key="publications-[^"]*".*?</section>', '', page)
    template = re.search(r'<div class="btn-wrapper"><a[^>]*_key="4e589343d8be".*?</a></div>', page).group()
    sections = ''.join(render_intro(m, template) for m in publications)
    anchor = '<section class="text-media right" data-key="80bdb76a9b67"'
    assert page.count(anchor) == 1
    page = page.replace(anchor, sections+anchor)
    pattern = r'(<script[^>]*id="__NUXT_DATA__"[^>]*>)(.*?)(</script>)'
    page = re.sub(pattern, lambda m: m[1]+update_payload(m[2], modules)+m[3], page)
    page_path.write_text(page)
    payload = PUB / '_payload.json'
    payload.write_text(update_payload(payload.read_text(), modules))
    for r in entries:
        folder = PUB / r['slug']
        folder.mkdir(exist_ok=True)
        (folder / 'index.html').write_text(report_page(r))
    print(f'Built {len(reports)} reports and one evidence dossier; static HTML, payload, and client modules updated.')


if __name__ == '__main__':
    main()
