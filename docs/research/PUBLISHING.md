# Publishing Kernellum reports

`publications.json` is the publication catalogue. The research page uses the
existing Nuxt `textIntro` component, including its typography, buttons, spacing
system and page lifecycle. There is no archive observer or DOM insertion script.

## Add a report

1. Put the final PDF in `docs/research/files/`.
2. Add an entry to `reports` in `publications.json`, following an existing entry.
   Use a new permanent `slug` and report ID. Include its publication date,
   summary, PDF filename, results, abstract and repository artifact links.
   `evidence` is the separate evidence dossier entry.
3. Run `python3 scripts/build_publications.py` from the repository root.
4. Run `python3 scripts/check_publications.py`.
5. Review the generated diff, direct research-page load, Home → Research
   navigation, a report page, its PDF, and browser Back on desktop and mobile.
6. Commit and push the resulting files through the normal website release flow.

The build orders reports newest-first and generates permanent detail pages,
PDF reading/download links, citation metadata and human-readable citations.
It synchronizes the static HTML, Nuxt's embedded/extracted payloads and client
content data. Repeated builds are byte-identical.

Do not add archive scripts to the global runtime, wrap History API methods, or
insert sections into Nuxt-owned DOM. The previous archive implementation used
that approach and was reverted. The compiled application, navigation and
animation code do not need modification to publish reports.

The original files keep their publication dates. Updating PDF typography does
not silently assign a new research date. New substantive revisions should be
identified explicitly in the catalogue and PDF.
