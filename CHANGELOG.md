# Changelog

## Unreleased

### Added
- `data/references.csv` (353 rows) — source publications parsed from the published
  supplementary reference list and matched to Crossref. 342 of 353 carry a DOI.
- `data/species.csv` (457 rows) — taxa resolved against Open Tree of Life with NCBI
  Taxonomy cross-check, full lineages, and curation flags.
- `legacy/` — frozen copies of the original working file, published supplement, and
  reference list.
- `data/species_traits.csv` (3,060 observations, 457 species, 23 traits) in long format,
  with `trait_definitions.csv` (scoring scope per trait) and `trait_vocabularies.csv`
  (controlled values). Traits are kept separate from `species.csv`: taxonomy is a resolved
  external fact, traits are observations with their own provenance and scoring scope.
- Repository scaffolding: schemas, governance, contribution routes.

### Notes
- 42 stored OTT ids were found not to match the taxon their name resolves to, including
  three keyed to hybrid taxa. See `docs/species_README.md`.
- 21 family names in the source file are misspellings; *Camellia sinensis* was filed under
  Brassicaceae.
- Six Crossref matches were rejected during manual review as wrong papers.
- `invasive` was only ever scored for animals in the source file. The blanket "n" on plants
  and fungi is an unscored default, not a negative observation, and is omitted rather than
  recorded as false.
- The source `Habitat` column held two variables (habitat for free-living species, host type
  for parasites); these are separated into `habitat` and `host_type`.
