# Changelog

## Unreleased

### Added
- `data/references.csv` (353 rows) — source publications parsed from the published
  supplementary reference list and matched to Crossref. 342 of 353 carry a DOI.
- `data/species.csv` (457 rows) — taxa resolved against Open Tree of Life with NCBI
  Taxonomy cross-check, full lineages, and curation flags.
- `legacy/` — frozen copies of the original working file, published supplement, and
  reference list.
- Repository scaffolding: schemas, governance, contribution routes.

### Notes
- 42 stored OTT ids were found not to match the taxon their name resolves to, including
  three keyed to hybrid taxa. See `docs/species_README.md`.
- 21 family names in the source file are misspellings; *Camellia sinensis* was filed under
  Brassicaceae.
- Six Crossref matches were rejected during manual review as wrong papers.
