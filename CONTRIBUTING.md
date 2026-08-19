# Contributions welcome

A single map or many, or genome size updates. 

## If you use GitHub

### 1. Use the issue form

You need a (free) GitHub account

Open a new issue, choose **Add a linkage map record**, fill in the form, submit.
You need: a DOI, a species name, sex-averaged map length in cM, marker count, number of
linkage groups, and haploid chromosome number. Everything else is optional.

Automated checks run when the issue is opened and re-run whenever you edit it, posting a
comment on the issue: the DOI is resolved against Crossref, the species name against the
Open Tree of Life taxonomy, and the numbers against plausibility ranges. The checks are
advisory — a curator then reviews the record and enters it (see `docs/curator_guide.md`).

### 2. A pull request (for many records at once)

1. Fork the repository.
2. Add rows to `data/maps.csv`, or drop a CSV into `inbox/`.
3. Run the checks locally: `python scripts/validate.py`
4. Open a pull request. Validation runs automatically and posts its report on the PR.

Do not edit anything in `derived/` — those files are rebuilt automatically.

## If you don't use GitHub

Download
[`templates/submission_template.xlsx`](templates/submission_template.xlsx), fill it in
(one row per map — the template contains instructions and a worked example), and email it
to the maintainer. A curator will submit it for you. You will still be credited.

## What makes a good record

- **One row per linkage map.** A species with three published maps gets three rows.
- **Sex-averaged map length** where available; use the sex-specific columns otherwise.
- **Say where the genome size came from** — assembly, flow cytometry, C-value — rather than
  leaving the method implicit.
- **Do not compute the recombination rate yourself.** It is calculated at build time from
  map length and genome size.
- **Uncertain?** Submit anyway and say so in the notes. Flagged is better than absent.

## Calculating sex-averaged maps
For species with **undifferentiated sex chromosomes (homogametic)**: the sex-averaged map length = (female map legnth + male map length)/2. 
For species with **differentiated sex chromosomes (XY,ZW,XO, a.k.a heterogametic)**: sex-averaged map length = sum of sex-averaged autosomes ((female map legnth + male map length)/2) + the length of the map for the homogemetic sex chromosome (Z,X).

## Credit

Add yourself to `data/contributors.csv` with your ORCID, or let a curator do it. Every
contributor appears as an author on the citable dataset releases.
