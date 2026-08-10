# `references.csv` — source publications

**451 rows, 29 fields.** One row per publication cited in the Stapley et al. (2017)
compilation. This is the first of the seven tables described in `recmapdb_plan.md` §3.
The original parse of the published supplement yielded 353 rows (described below); a
2026 recovery campaign traced the sources of the working-file records that were not in
the published reference list, adding 98 further publications. Each recovered row carries
`match_confidence = recovered_2026` and a `review_note` naming its evidence; the audit
trail is in `docs/references_recovered_2026.csv`. Only 2 of 486 map records still lack a
reference (see `docs/missing_references_worklist.csv`).

## Provenance

Built from the published supplementary reference list
(`rstb20160455_si_003.pdf`), parsed to 353 entries, matched to Crossref, and enriched with
full bibliographic metadata retrieved by DOI. The verbatim citation text is kept in
`citation_verbatim` for every record, so no downstream field requires trusting the
automated match — a curator can always check against the source string.

## Coverage

| Field | Populated |
|---|---|
| `ref_id`, `authors`, `title`, `year` | 353 (100%) |
| `journal` | 349 (99%) |
| `volume` | 348 (99%) |
| `doi` | 342 (97%) |
| `issue` | 322 (91%) |
| `pages` | 250 (71%) |

Sources span 1998–2017 (median 2013) across
90 journals; *BMC Genomics* (49), *G3* (28) and
*Genetics* (20) are the most frequent.

Page ranges are the weakest field at 71%. Crossref simply does not carry `page` for many
article-numbered journals (BMC, PLOS, Scientific Reports), so this is a limitation of the
upstream metadata rather than of the parsing — for those journals the article number in
`doi` is the locator that matters.

## Key design points

**`ref_id` is the primary key**, not the row number. It is a citekey — lowercase
first-author surname plus year (`butcher2000`, `hawthorne2001a`), with letter suffixes
where the same author published in the same year. It is stable, human-readable in a diff,
and directly usable as a BibTeX key. `si_ref_number` is retained as the join key back to
`SuppDat.csv`.

**One reference can serve several map records.** Two DOIs each cover two species
(`10.1371/journal.pone.0145144` for *Eucalyptus tereticornis* and *E. urophylla*;
`10.1534/g3.114.012096` for *Lucania goodei* and *L. parva*). This is why `references.csv`
is a separate table joined many-to-one from `maps.csv` rather than columns on the map row.

**Match evidence travels with the data.** `match_confidence`, `match_title_score`,
`match_author_score`, `manual_review` and `review_note` record how each DOI was arrived at:
330 automatic high-confidence matches, 12 verified or supplied by hand, 11 with no DOI. Six
candidate matches were rejected during review as wrong papers — that audit trail is in
`review_note`.

**Three QC flags are shipped, not silently fixed.**

- `flag_year_mismatch` (41 records) — the supplement year disagrees with the DOI record.
  Mostly off-by-one from online-ahead-of-print; references 156/157 (*Haplochromis*, Henning)
  have their years transposed. These need adjudication, and the rule should be documented:
  the recommendation is to treat the Crossref year as authoritative and keep `si_year` for
  traceability.
- `flag_no_doi` (11 records) — pre-DOI-era papers, non-indexed journals, and citations
  truncated in the source PDF. Bibliographic fields for these were transcribed from the
  citation text by hand; four have no recoverable journal because the PDF cut the citation
  short.
- `flag_author_list_incomplete` (1 record) — Crossref lists materially fewer authors than
  the citation.

**`journal_normalized`** unifies known surface variants (PLoS ONE / PLOS ONE, G3 with and
without a colon) for grouping; `journal` preserves exactly what Crossref returned.

## Files

- `references.csv` — the table
- `references.schema.json` — Frictionless Table Schema: types, constraints, enums,
  per-field descriptions. Validates clean against the CSV.
- `references.bib` — BibTeX export, 353 entries keyed by `ref_id`
- `species_reference_link.csv` — the 353 published species mapped to `ref_id` and DOI
- `working_file_reference_link.csv` — all 486 working-file rows; 381 linked to a `ref_id`,
  370 with a DOI, 105 flagged `needs_reference`

## Known issues for the curator

1. **41 year discrepancies** need a documented resolution rule.
2. **`si_ref_number` 239** is "Rogers" in the data file and "Cox" in the reference list.
3. **`martinello2005`** — the citation's first author is Martinelli, A.; the data file says
   "Martinello". The `ref_id` follows the data file for continuity; worth correcting.
4. **105 working-file records** (species added after the paper) still have no reference.
   These are the crowdsourcing candidates described in the plan.
