# Publishing Kernellum research

The public research archive at `/research/` is data-driven.

## Add a report

1. Place the finalized PDF in `docs/research/reports/`.
2. Add one object to `docs/research/reports.json`.
3. Use the actual breakthrough/result date in both `date` and `dateISO`.
4. Keep `id` stable after publication.
5. Set `published` to `true`.

The existing research-page layout and generated Nuxt markup do not need to be edited for future reports.

## Manifest fields

- `id`: stable public report identifier, e.g. `TR-004`
- `type`: public document type
- `date`: display date
- `dateISO`: sortable ISO date
- `title`: report title
- `summary`: one-sentence archive description
- `result`: compact evidence/result line
- `pdf`: path relative to `docs/research/`
- `published`: visibility flag

Numbered technical reports belong in `reports`. Evidence/control documents belong in `evidence`.

## UI contract

`publications.js` mounts the archive only after the existing page has loaded.
`publications.css` is fully namespaced under `.krn-publications` and uses the website's existing typography and color tokens.
Do not add global selectors to the publication stylesheet.
