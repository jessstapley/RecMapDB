# Changelog

## Unreleased

### Added
- `data/maps.csv` (486 rows) — the core observation table, one row per linkage map per
  study, keyed to species.csv and references.csv, with per-record quality flags.
- `data/genome_sizes.csv` (637 estimates) — one row per genome-size estimate per species,
  each with its measurement method; maps.csv names which estimate it used.
- `data/recombination_rates.csv` (430 rows) — DERIVED. Rebuilt by scripts/build_derived.py;
  CI fails if it has drifted from maps.csv.
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

### Verified
- Recomputing the rate from map length and genome size reproduces the stored RR column
  exactly on all 430 computable rows.
- `passes_2017_criteria` reproduces the published subset: all 353 records in the published
  supplement pass, and `in_published_353` matches the supplement exactly.

### Notes
- 42 stored OTT ids were found not to match the taxon their name resolves to, including
  three keyed to hybrid taxa. See `docs/species_README.md`.
- 21 family names in the source file are misspellings; *Camellia sinensis* was filed under
  Brassicaceae.
- Six Crossref matches were rejected during manual review as wrong papers.
- `invasive` was only ever scored for animals in the source file. The blanket "n" on plants
  and fungi is an unscored default, not a negative observation, and is omitted rather than
  recorded as false.
- All trait vocabulary values are now defined. The opaque source codes (heterochiasmy H/A,
  karyotype H, genotypic MH/FH, plant life form P/PA) were supplied by the compiler.
- 163 trait values carry a primary literature citation, recovered from the Tree of Sex
  datasets in `Sex_data/`. Where both sources have a value they agree exactly (35/35
  karyotype, 34/34 genotypic); 13 values absent from the compilation were added.
- Corrected: `Allium cepa` and `Lactuca sativa` carried "SC" (a Selfing value) in the
  genotypic sex-determination column. Both rows removed.
- The source `Habitat` column held two variables (habitat for free-living species, host type
  for parasites); these are separated into `habitat` and `host_type`.
