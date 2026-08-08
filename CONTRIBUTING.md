# Contributing

Three ways to add data, from easiest to most involved.

## 1. The issue form (no git needed)

Open a new issue, choose **Add a linkage map record**, fill in the form, submit.
You need: a DOI, a species name, sex-averaged map length in cM, marker count, number of
linkage groups, and haploid chromosome number. Everything else is optional.

Automated checks run immediately and comment on the issue: the DOI is resolved against
Crossref, the species name against the Open Tree of Life taxonomy, and the numbers against
plausibility ranges. A curator then reviews and merges.

## 2. A pull request (for many records at once)

1. Fork the repository.
2. Add rows to `data/maps.csv`, or drop a CSV into `inbox/`.
3. Run the checks locally: `python scripts/validate.py`
4. Open a pull request.

Do not edit anything in `derived/` — those files are rebuilt automatically.

## 3. Send a spreadsheet

If you would rather not use GitHub, download `templates/submission_template.xlsx`, fill it
in, and email it to the maintainers. A curator will submit it for you. You will still be
credited.

## What makes a good record

- **One row per linkage map.** A species with three published maps gets three rows.
- **Sex-averaged map length** where available; use the sex-specific columns otherwise.
- **Say where the genome size came from** — assembly, flow cytometry, C-value — rather than
  leaving the method implicit.
- **Do not compute the recombination rate yourself.** It is calculated at build time from
  map length and genome size.
- **Uncertain?** Submit anyway and say so in the notes. Flagged is better than absent.

## Credit

Add yourself to `data/contributors.csv` with your ORCID, or let a curator do it. Every
contributor appears as an author on the Zenodo dataset release.
