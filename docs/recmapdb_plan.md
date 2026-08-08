# A community-curated database of eukaryote linkage-map recombination rates

**Plan prepared for:** Jessica Stapley
**Source paper:** Stapley et al. (2017) *Phil. Trans. R. Soc. B* — "Variation in recombination frequency and distribution across eukaryotes"
**Source data:** `RecRate_Data/LinkageMapIinfo2.csv` (486 rows x 66 columns), published subset `SuppDat.csv` (353 species)
**Working name used below:** `recmapdb` (placeholder — see §11)

---

## 0. Recommendation in one paragraph

Publish the data as **plain CSV files in a public GitHub repository**, normalised into a
small number of linked tables, documented with a machine-readable schema
(Frictionless Data Package), released as versioned tags that mint a **Zenodo DOI**, and
served to non-technical users through a **GitHub Pages site** with a searchable table.
Accept new records through a **GitHub Issue Form** (a web form — contributors need no
git skills) that a bot converts into a pull request; validate every submission
automatically with **GitHub Actions** (schema, units, plausible ranges, taxon-name
resolution, DOI resolution, duplicate detection); merge after a short human curation
check. Credit every contributor in a `contributors.csv` that feeds the Zenodo author
list, so contributing earns a citable authorship. Budget roughly **6–10 weeks of
part-time work to v1.0**, with the largest single chunk being the one-off cleaning and
re-structuring of the existing file (§2–§3), not the software.

The rest of this document works through the reasoning, the concrete design, and a phased
roadmap.

---

## 1. Audit of the current data file

These numbers come from reading `LinkageMapIinfo2.csv` directly; they set the agenda for
what has to be fixed before the file becomes a public database.

| Observation | Detail | Consequence |
|---|---|---|
| Size | 486 rows, 66 columns; 457 distinct species | The working file is a superset of the 353 species published in the supplement — it contains records that failed the paper's inclusion criteria plus later additions. Which is which is not recorded in the file. |
| Repeated species | 29 species appear twice (e.g. *Zea mays*, *Gallus gallus*, *Gasterosteus aculeatus*) | The unit of observation is **a linkage map**, not a species. The schema must say so explicitly, and a rule is needed for which map is "preferred" for cross-species analyses. |
| Broken derived column | `RR` is stored as text; 56 rows contain the Excel error string `#VALUE!`, all of them rows where genome size is missing | Derived values should never be stored — recompute them in the build step. Where the 430 computable values exist they agree exactly with `MapLength.cM / combined.Gsize`, so the formula is unambiguous. |
| Provenance | `Ref` holds only a first-author surname; `year` holds a year. 400 distinct author+year combinations for 486 rows | No DOI, no title, no journal in the working file itself. **Largely solved** — the full citations live in the published supplement `rstb20160455_si_003.pdf` and have now been parsed and resolved to DOIs (§1a). |
| Genome size | Four partly redundant columns: `Size.Mb` (254), `Cval` (185), `est.Gsize.Mb` (402), `combined.Gsize` (430) | The value used in the rate is a mixture of measurement types with no per-record record of *which* method and *which* source. 56 records have no genome size at all and therefore no rate. |
| Column naming | `MarkerInterval ` has a trailing space; `RR_Mb.cM` holds values in cM/Mb (the name is inverted); `av.sex` takes values `n/y/m/f`; nine near-duplicate taxonomic grouping columns (`newGroup`, `newSubGroup`, `newSubGroup2`, `newSubGrp2`, `newSubGroupClade`, ...) | Names and codes that were shorthand for one analysis become a maintenance burden the moment a stranger has to fill them in. |
| Sparse trait columns | 21 columns are species-level traits, many <40% complete (`plant.LifeForm` 3.9%, `LeafPhenology` 14.4%), several are plant-only | Traits belong in their own table with their own provenance, otherwise the core table is mostly empty cells and contributors do not know which fields they are expected to fill. |
| Inclusion criteria not stored | The paper excludes maps with <50 markers and with `abs(LG − HCN)/HCN > 0.7`. Applying those rules to the current file flags 13 and 23 records respectively | These are *analysis filters*, not data errors. Store the raw record plus a computed quality flag; let users filter. This is what lets the database serve analyses other than the 2017 one. |

**Design consequence.** The file is a well-organised *analysis worksheet*, and it should
now be split into what a database needs: an observation table with one row per linkage
map, lookup tables for the things that are properties of a species or of a study, and a
build step that regenerates every derived column. A draft field-by-field disposition of
all 66 columns is provided as `data_dictionary_draft.csv` (see §12).

### 1a. Provenance: resolved

The 353 full citations were recovered from the published supplementary reference list
(`rstb20160455_si_003.pdf`) and matched to Crossref. This closes what was the largest gap
in the audit above.

| | n | % |
|---|---|---|
| References parsed from the PDF | 353 / 353 | 100% |
| Matched to a DOI automatically (high confidence) | 330 | 93% |
| Matched after manual verification | 12 | 3% |
| Unresolved (no DOI found) | 11 | 3% |
| **Total with DOI** | **342** | **97%** |

Matching used a Crossref bibliographic query per reference, scored on fuzzy title
similarity, first-author surname agreement, and year proximity; 12 borderline matches were
checked by hand against the Crossref record and 6 were rejected as wrong papers. The
verbatim citation text is retained for every record so nothing depends on trusting the
match.

**Linking to the data.** `SuppDat.csv` carries a `Ref.number` column keyed to this list, so
the join is exact — all 353 published species link to their reference, and first-author
surnames agree for 352 of 353 (`Ref.# 239` is listed as "Rogers" in the data and "Cox" in
the reference list; worth a look). Propagating through species gives **370 of the 486
working-file records (76%) a DOI immediately**. The remaining 116 fall into two groups:
105 records for species that were never in the published set (added after 2017), which
need references supplied by hand; and 11 records whose species *is* in the published 353
but whose reference is one of the 11 still-unresolved DOIs — those are the manual-lookup
worklist below, not a separate category of work.

**Two useful things fell out of the matching.** First, 41 records have a year in the
supplement that disagrees with the year on the DOI record — mostly off-by-one, but
references 156 and 157 have their years transposed. Second, two DOIs are each used by two
records (`10.1371/journal.pone.0145144` for *Eucalyptus tereticornis* and *E. urophylla*;
`10.1534/g3.114.012096` for *Lucania goodei* and *L. parva*). Those are single papers
reporting maps for two species — direct confirmation of the design decision in §2 that the
row is a map, not a study, and that `references.csv` must be a separate table joined
many-to-one.

**What this does to the roadmap.** Phase 1 step 3 ("resolve references to DOIs"), estimated
above as the slowest task in the whole project, is now largely done. What remains is
11 manual lookups (`references_unresolved_worklist.csv` — mostly pre-DOI-era papers, a
thesis, and non-indexed journals), the year discrepancies, and references for the 105
post-2017 working-file records. That last group is a good candidate for the crowdsourcing
route described in §7: one issue per record, an easy first contribution.

---

## 2. Design principles

1. **One row = one linkage map from one study.** Not one row per species. A species with
   three published maps has three rows; cross-species analyses pick one via a documented
   rule (most markers, then most individuals — the paper's own rule) that the build step
   applies and records in a `preferred_map` column.
2. **Store what was measured; compute what was derived.** `map_length_cM`,
   `n_markers`, `genome_size_mb` are stored. Recombination rate, marker interval, and the
   female/male ratio are computed by a script at build time and shipped in a *derived*
   file. A contributor can never introduce an arithmetic error, and if the definition of
   the rate changes, one line of code changes.
3. **Every value carries its source.** Each map record carries a reference DOI; each
   genome-size value carries a source and a method. This is the difference between a
   dataset people cite and a dataset people trust.
4. **Filter, do not delete.** Records that fail the 2017 inclusion criteria stay in the
   database with quality flags attached. Different questions warrant different filters.
5. **Text files, plain CSV, in git.** No binary formats, no database server. A CSV diff in
   a pull request is human-readable, which is what makes community review possible at
   all. Excel is a source of silent corruption (`#VALUE!`, date coercion of gene names,
   invisible trailing spaces) and should be an export target, never the master.
6. **Machine-readable schema.** A `datapackage.json` (Frictionless Table Schema) that
   declares every field's type, unit, allowed values, and constraints. Validation, the
   documentation website, and the submission form all generate from this one file.
7. **Low barrier at the front, strict checks behind.** Contributors should be able to add a
   record from a web form in five minutes. The strictness lives in automated validation
   and curator review, not in the form.

---

## 3. Proposed data model

Seven CSV files. All keys are stable, opaque, and never reused.

```
maps.csv              one row per linkage map      PK map_id      (RM0001, RM0002, ...)
species.csv           one row per taxon            PK ott_id
references.csv        one row per study            PK ref_id      (doi-derived slug)
genome_sizes.csv      one row per genome-size estimate           FK ott_id, source
species_traits.csv    long format: ott_id, trait, value, source  
contributors.csv      one row per person           PK orcid
vocabularies/*.csv    one file per controlled field: value, definition
```

### 3.1 `maps.csv` — the core table

| field | type | unit | required | notes |
|---|---|---|---|---|
| `map_id` | string | | yes | Assigned by curator on merge; permanent. |
| `ott_id` | string | | yes | Open Tree taxon id → `species.csv`. |
| `ref_id` | string | | yes | → `references.csv`. |
| `map_length_cM` | number | cM | yes | Sex-averaged sum of all linkage groups. |
| `map_sex` | enum | | yes | `sex_averaged` / `female` / `male` / `unknown`. |
| `map_length_female_cM` | number | cM | no | |
| `map_length_male_cM` | number | cM | no | |
| `n_markers` | integer | | yes | |
| `n_linkage_groups` | integer | | yes | |
| `haploid_chromosome_number` | integer | | yes | |
| `mapping_population_n` | integer | | no | |
| `cross_type` | enum | | no | F2, backcross, pedigree, RIL, ... — **new field, worth adding** |
| `marker_type` | enum | | no | RAD, SNP array, SSR, AFLP, WGS — **new field** |
| `mapping_software` | string | | no | **new field**; affects map length systematically |
| `genome_size_mb` | number | Mb | no | The value used; resolved from `genome_sizes.csv`. |
| `genome_size_source_id` | string | | no | Which estimate was used. |
| `rate_as_published_cM_per_Mb` | number | cM/Mb | no | As stated by the source study, for cross-checking. |
| `assembly_accession` | string | | no | **new field**; GCA/GCF, links the map to a genome. |
| `notes` | string | | no | Free text. |
| `contributor_orcid` | string | | yes | Who submitted it. |
| `date_added` | date | | yes | Set by CI. |

Three additions are worth arguing for. `cross_type`, `marker_type` and
`mapping_software` are known to shift estimated map length (dense SNP maps in modern
software give systematically different lengths from sparse AFLP maps), and a database
that spans 1998–2026 will need them to model that heterogeneity. They can be left blank
for legacy records and required for new submissions.

### 3.2 Derived outputs, rebuilt on every release

`recombination_rates.csv` = `maps.csv` joined to species and genome size, plus:

- `recombination_rate_cM_per_Mb` = `map_length_cM / genome_size_mb`
- `marker_interval_cM` = `map_length_cM / n_markers`
- `fm_ratio` = female/male map length
- `qc_few_markers` = `n_markers < 50`
- `qc_lg_hcn_mismatch` = `abs(n_linkage_groups − haploid_chromosome_number) / haploid_chromosome_number > 0.7`
- `passes_2017_criteria` = neither flag set (reproduces the published subset)
- `preferred_map` = TRUE for the best map per species under the documented rule

Shipping `passes_2017_criteria` is what makes the database backwards-compatible with the
published paper: anyone can reproduce the 2017 figures from the live database and see
exactly what has changed since.

### 3.3 Why not a "real" database (Postgres, SQLite server, an API)?

For a table of this size — hundreds to low thousands of rows, growing by tens per year — a
server-backed database buys nothing and costs a maintainer. Git gives version history,
diffs, review, rollback, and offline copies for free. If a query interface is wanted
later, `datasette` can serve a SQLite file built from the CSVs on every release, hosted
free on Fly.io or Vercel; that is an add-on, not a foundation. Start file-based.

---

## 4. Repository layout

```
recmapdb/
├── README.md                     what it is, how to cite, how to contribute
├── LICENSE                       CC0-1.0 or CC-BY-4.0 for data
├── LICENSE-CODE                  MIT for scripts
├── CITATION.cff                  machine-readable citation
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md               the single most-read file; keep it short
├── GOVERNANCE.md                 who decides, how curators are added
├── CHANGELOG.md                  what changed in each release
├── datapackage.json              Frictionless schema for every table
├── data/
│   ├── maps.csv
│   ├── species.csv
│   ├── references.csv
│   ├── genome_sizes.csv
│   ├── species_traits.csv
│   ├── contributors.csv
│   └── vocabularies/*.csv
├── derived/                      built by CI, never hand-edited
│   ├── recombination_rates.csv
│   └── recmapdb.sqlite
├── inbox/                        one CSV per pending submission, staged by the bot
├── scripts/
│   ├── validate.py               all checks, runnable locally
│   ├── build.py                  derived tables + sqlite
│   ├── resolve_taxa.py           OTT / GBIF / NCBI name resolution
│   └── make_zenodo_metadata.py   contributors.csv -> .zenodo.json
├── .github/
│   ├── ISSUE_TEMPLATE/add_record.yml
│   ├── workflows/validate.yml
│   ├── workflows/issue_to_pr.yml
│   └── workflows/release.yml
├── docs/                         Quarto site -> GitHub Pages
└── legacy/
    ├── LinkageMapIinfo2.csv      the original file, frozen, for provenance
    └── stapley2017_supplement.csv
```

Keeping the original file in `legacy/` unchanged matters: it lets anyone verify that the
restructuring preserved the published values.

---

## 5. How people add data — three routes

### Route A: GitHub Issue Form (the default; no git required)

A YAML issue form gives contributors a proper web form with dropdowns and required
fields. They click "New issue → Add a linkage map", fill it in, submit. Sketch:

```yaml
name: Add a linkage map record
description: Submit recombination data for one linkage map
labels: [new-record]
body:
  - type: input
    id: doi
    attributes: {label: DOI of the study, placeholder: "10.1111/mec.12345"}
    validations: {required: true}
  - type: input
    id: species
    attributes: {label: Species (binomial), placeholder: "Daphnia magna"}
    validations: {required: true}
  - type: input
    id: map_length_cM
    attributes: {label: Sex-averaged map length (cM)}
    validations: {required: true}
  - type: dropdown
    id: map_sex
    attributes: {label: Map sex, options: [sex_averaged, female, male, unknown]}
    validations: {required: true}
  - type: input
    id: n_markers
    attributes: {label: Number of mapped markers}
    validations: {required: true}
  # ... n_linkage_groups, haploid_chromosome_number, genome size + source,
  #     cross_type, marker_type, mapping_software, assembly accession, ORCID
```

A GitHub Action parses the issue body into a row, writes `inbox/<issue>.csv`, opens a pull
request, runs validation on it, and posts the validation report back as a comment on the
issue so the contributor sees immediately whether the DOI resolved and the species name
matched. This is the pattern used by community datasets like the Leipzig Catalogue of
Vascular Plants and AusTraits, and it works: contributors get a form, curators get a
reviewable diff.

### Route B: Pull request (for people who bring 50 records)

Contributors fork, append rows to `data/maps.csv` (or drop a file in `inbox/`), and open a
PR. The same validation runs. `CONTRIBUTING.md` gives the copy-paste git commands and a
blank template CSV.

### Route C: Bulk / non-GitHub submission

A spreadsheet template (`templates/submission_template.xlsx` with data-validated
dropdowns) that people email or upload via a Google Form. A curator runs
`scripts/validate.py` locally and opens the PR on their behalf. This route matters more
than it looks — a substantial fraction of the people holding relevant unpublished maps
will not have a GitHub account, and the cost of losing their data is higher than the cost
of a curator doing five minutes of clerical work.

Whichever route, the submitter's ORCID is recorded and they are added to
`contributors.csv`.

---

## 6. Automated validation

`scripts/validate.py` runs on every PR (GitHub Actions), and contributors can run it
locally. Checks, in order of how often they will fire:

**Structural**
- Frictionless schema validation: types, required fields, enum membership against
  `vocabularies/`, uniqueness of `map_id`.
- No new columns, no reordered columns, UTF-8, LF line endings, no trailing whitespace.

**Referential**
- `ott_id` exists in `species.csv`; `ref_id` exists in `references.csv`; every genome-size
  reference resolves.

**Plausibility (the checks that catch real errors)**
- `map_length_cM` within, say, 20–20 000 cM — flags unit confusion (Morgans entered as cM,
  or a per-chromosome length entered as a whole-map length).
- `n_linkage_groups` within a factor of 2 of `haploid_chromosome_number`.
- `n_markers >= n_linkage_groups`.
- Computed rate within 0.05–100 cM/Mb; outside that, the record is flagged for curator
  attention rather than rejected.
- If `rate_as_published` is given, it must agree with the computed rate to within 10% —
  this catches a wrong genome size very effectively.

**External resolution**
- DOI resolves via the Crossref API; title and authors are fetched and written into
  `references.csv` automatically, so contributors only ever type a DOI.
- Species name resolves against Open Tree of Life (matching the existing `ott_id` scheme)
  with GBIF and NCBI as cross-checks; synonyms are reported, not silently accepted.
- Optional: genome size cross-checked against the Genome Size Databases / NCBI assembly
  when an accession is given.

**Duplicate detection**
- Same DOI + same species already present → block and point at the existing `map_id`.
- Same species, map length within 2%, marker count within 5% → warn ("this may be the
  same map published twice").

The Action posts a single tidy comment: green ticks, warnings, and blockers. Blockers
prevent merge; warnings need a curator to tick a box.

```yaml
# .github/workflows/validate.yml (sketch)
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install frictionless pandas requests
      - run: python scripts/validate.py --report report.md
      - uses: marocchino/sticky-pull-request-comment@v2
        with: {path: report.md}
```

---

## 7. Curation and governance

Automation catches syntax; it cannot catch "this map is the same population as RM0104
reanalysed". Budget for human review.

- **Roles.** *Contributor* (submits), *Curator* (reviews and merges; 2–4 people), *Steering
  group* (decides scope, schema changes, authorship policy; 3–5 people including you as
  lead). Write this into `GOVERNANCE.md` on day one — governance documents written after
  the first disagreement are much harder to write.
- **Curator checklist** (a PR template): reference is a primary source; map is not already
  in the database under another reference; genome size method is appropriate for the
  species; quality flags are correct; contributor added to `contributors.csv`.
- **Service level.** State a realistic one, e.g. "we aim to review submissions within one
  month". An unstated expectation is always violated.
- **Schema changes** require an issue, a two-week comment period, and a minor version bump.
  Renaming a column silently is the fastest way to break every downstream script.
- **Corrections.** Any user can open an issue against an existing `map_id`. Corrections are
  logged in `CHANGELOG.md` against the record — a database that visibly fixes itself is
  more trustworthy than one that never appears to change.
- **Realistic load.** Expect a burst at launch (data-paper publicity), then perhaps 20–60
  records a year. That is a few hours a month, if the automation carries the routine work.

---

## 8. Releases, DOIs and credit

- **Versioning.** `MAJOR.MINOR.PATCH` on the data: MAJOR = breaking schema change, MINOR =
  new records, PATCH = corrections. Tag each release in git.
- **Zenodo.** Enable the GitHub–Zenodo integration once; every tagged release then mints a
  version DOI automatically and the *concept DOI* always resolves to the latest version.
  Cite the concept DOI in papers about the database, the version DOI in analyses.
- **Author list as credit.** `scripts/make_zenodo_metadata.py` regenerates `.zenodo.json`
  from `contributors.csv` before each release, so **every contributor appears as an author
  on the citable dataset record, with their ORCID**. This is the incentive that makes
  people contribute; make it explicit in the README. (The IBEX Imaging Knowledge-Base uses
  exactly this expanding-byline model.)
- **A data paper.** Once v1.0 is out, a short descriptor in *Scientific Data*, *Molecular
  Ecology Resources*, or *Ecology and Evolution* gives contributors a conventional paper to
  cite and drives the initial submissions. Contributors up to v1.0 become co-authors; later
  contributors accrue on the Zenodo byline. Decide and publish this rule before launch.
- **License.** **CC0-1.0** for the data (maximum reuse, no attribution-stacking problems
  when aggregated) with a stated *citation norm* in the README, or **CC-BY-4.0** if you
  prefer attribution to be legally binding. Both are acceptable to journals and funders;
  CC0 is the norm for aggregated compilations like this. Code MIT.

---

## 9. Making the data usable

- **Direct URLs.** Every CSV has a permanent raw URL, so `read.csv("https://raw.github.../maps.csv")`
  works in one line from R or Python. Document this in the README — it is the feature most
  users will actually use.
- **Website.** A Quarto site published to GitHub Pages: landing page, searchable/filterable
  table (`reactable` or `DT`), the data dictionary rendered from `datapackage.json`, a
  taxon-coverage figure and rate-distribution figure rebuilt from the current data on every
  release, and a page reproducing the 2017 figures from live data.
- **R package (later).** A thin `recmapdb` R package with `rm_maps()`, `rm_rates()`,
  `rm_version()` that downloads from a pinned Zenodo release and caches locally. AusTraits'
  R package is the model. Worth doing only once the data is stable — v1.1, not v1.0.
- **Interoperability.** Use Darwin Core terms where they exist (`scientificName`,
  `taxonID`) so the dataset can eventually be harvested by biodiversity aggregators.

---

## 10. Risks and how to blunt them

| Risk | Mitigation |
|---|---|
| Nobody contributes | Seed with 50–100 post-2017 maps yourself so the database is visibly alive; publish the data paper; announce on Evoldir, relevant societies, and at a conference; make the authorship incentive prominent. |
| Maintainer bus factor | 2+ curators from the start; everything in a public repo; governance document; the whole thing survives on free infrastructure with no server to pay for. |
| Scope creep (LD-based maps, fine-scale landscapes, pedigree-based rates) | Write the scope into README v1: *sex-averaged, genome-wide, linkage-map-derived rates*. Add other estimate types later as separate tables with an `estimate_method` field, not by widening `maps.csv`. |
| Schema churn breaking users | Versioned releases + deprecation policy; never repurpose a column name. |
| Low-quality submissions | Validation + curator review + quality flags rather than rejection; reviewers can see the diff. |
| Duplicated/derivative maps | Automated near-duplicate detection plus an explicit `supersedes` field for reanalyses of the same cross. |

---

## 11. Naming

`recmapdb` is a placeholder. Alternatives worth considering: **RecMapDB**, **OpenRecMap**,
**EuRec** (Eukaryote Recombination), **LinkMapDB**. Choose something searchable and not
already taken on GitHub/CRAN before the first public commit — renaming after the DOI is
minted is painful.

---

## 12. Phased roadmap

**Phase 0 — decisions (1 week, mostly yours)**
Name; license (CC0 vs CC-BY); scope statement; who the initial curators are; whether
`cross_type`/`marker_type`/`mapping_software` are added; authorship rule for the data
paper.

**Phase 1 — clean and restructure the existing data (2–4 weeks; the real work)**
1. Split the 66 columns into the seven tables per `data_dictionary_draft.csv`.
2. Recode opaque codes (`av.sex` → sex_averaged/female/male; `n`/`y` → TRUE/FALSE) and
   write the controlled vocabularies with definitions.
3. **Resolve references to DOIs — largely complete (§1a).** 342 of the 353 published
   references now carry a DOI (`references_resolved.csv`). Remaining work: 11 manual
   lookups, 41 year discrepancies to adjudicate, and references for the 105 working-file
   records that post-date the paper. The last group suits the crowdsourcing route in §7
   — one issue per record ("add a reference for RM0132"), an easy first contribution.
4. Attach method + source to every genome-size value.
5. Drop the stored `RR` column and its 56 `#VALUE!` cells; recompute in the build step.
6. Verify: the build must reproduce the 353-species published subset and its figures.

**Phase 2 — repository and automation (1–2 weeks)**
Repo skeleton, `datapackage.json`, `validate.py`, `build.py`, the three workflows, the
issue form, README/CONTRIBUTING/GOVERNANCE, `legacy/` snapshot.

**Phase 3 — public launch (1 week + review time)**
Tag v1.0.0 → Zenodo DOI → GitHub Pages site live → seed 50–100 new records → announce →
submit the data paper.

**Phase 4 — growth (ongoing)**
R package; Datasette query endpoint; DOI-completion campaign; annual release with a
refreshed contributor byline.

---

## 13. Companion file

Three files accompany this plan.

`references_resolved.csv` — all 353 published references with verbatim citation, parsed
title/journal/year, resolved DOI, match confidence, and per-record review notes.
`references_unresolved_worklist.csv` — the 11 needing manual lookup.
`working_file_doi_coverage.csv` — every working-file row with its reference number and DOI
where one could be propagated.

`data_dictionary_draft.csv` accompanies this plan: all 66 current columns with their
completeness, their proposed destination table and field name, unit, type, and a
disposition (`keep` / `rename` / `move` / `merge` / `derive` / `drop`) with notes. It is
the working document for Phase 1 — the sensible next step is for you to go through it and
overrule me where I have guessed wrong about what a column means (`corbett`, `check`,
`CorrectedRR`, `RI_status` and the `newSubGroup*` family are the ones I am least sure of).
