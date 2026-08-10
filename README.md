# recmapdb — an open database of eukaryote recombination rates from linkage maps

**Status: pre-release (v0.x). Schema may still change.**

Genome-wide recombination rate estimated from published linkage maps, across eukaryotes.
Seeded from the compilation in Stapley et al. (2017) *Phil. Trans. R. Soc. B*
[doi:10.1098/rstb.2016.0455](https://doi.org/10.1098/rstb.2016.0455) and designed to be
extended by the community.

## What is here now

| File | Rows | Description |
|---|---|---|
| `data/maps.csv` | 493 | **The core table.** One row per linkage map per study |
| `data/species.csv` | 459 | Taxa resolved against Open Tree of Life, cross-checked against NCBI |
| `data/references.csv` | 458 | Source publications, 97% with resolved DOIs; every map referenced |
| `data/genome_sizes.csv` | 639 | Genome-size estimates with method; 406 in use, covering 408 of 459 species |
| `data/species_traits.csv` | 3,071 | Species traits in long format, 163 with a primary citation |
| `data/recombination_rates.csv` | 437 | **Derived** — rebuilt from maps and genome sizes; do not edit |

Still to come: `contributors.csv`. See `docs/recmapdb_plan.md` for the full design.

## The headline quantity

Recombination rate is **not stored**. It is computed from what was measured:

    recombination_rate_cM_per_Mb = map_length_cM / genome_size_mb

so a corrected genome size propagates automatically. `scripts/build_derived.py` rebuilds
the derived table and CI fails if the committed version has drifted from its inputs.

To reproduce the published analysis: `maps[maps.passes_2017_criteria]`. All 353 records in
the published supplement pass; records that fail are kept and flagged, not deleted.

## Reading the data

```r
refs <- read.csv("https://raw.githubusercontent.com/USER/recmapdb/main/data/references.csv")
spp  <- read.csv("https://raw.githubusercontent.com/USER/recmapdb/main/data/species.csv")
```

```python
import pandas as pd
spp = pd.read_csv("https://raw.githubusercontent.com/USER/recmapdb/main/data/species.csv")
```

Each table has a Frictionless Table Schema beside it (`*.schema.json`) giving types,
constraints and a description of every field.

## Principles

1. **One row = one linkage map from one study**, not one row per species.
2. **Store what was measured; compute what was derived.** Recombination rate is
   recalculated at build time, never stored by hand.
3. **Every value carries its source.** Maps carry a reference DOI; genome sizes carry a
   method and a source.
4. **Filter, do not delete.** Records that fail any given inclusion criterion stay, with
   quality flags attached.
5. **Plain CSV in git**, so that every change is a readable diff.

## Contributing

New records are welcome — a single map or a hundred. See `CONTRIBUTING.md`. The quickest
route is the *Add a linkage map* issue form, which needs no git knowledge.

Contributors are credited as authors on the citable dataset release.

## Provenance

`legacy/` holds the original files unchanged: the working compilation
(`LinkageMapIinfo2.csv`), the published supplement, and the supplementary reference list.
Anyone can verify that the restructuring preserved the published values.

## Licence

Data: CC0-1.0. Code: MIT. See `LICENSE` and `LICENSE-CODE`.
