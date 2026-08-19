# `maps.csv` — the core observation table

**493 rows, 27 fields.** One row per linkage map from one study. Fourth table in the plan
(§3), and the one the rest of the database exists to support.

Two companions land with it: `genome_sizes.csv` (683 estimates) and the derived
`recombination_rates.csv` (430 rows).

## The unit of observation is a map

29 species have more than one published map. Each gets its own row, its own `map_id`, its
own reference and its own quality flags. `Cynodon dactylon` is the clearest case: two maps
from the same 2010 study, one with n = 9 and 36 markers, one with n = 18 and 125 markers —
a polyploid series, not a contradiction. The first fails the marker criterion; the second is
the one that appeared in the published analysis.

## The sex-averaged map length 

For species with undifferentiated sex chromosomes (homogametic): if you have a male and female specific map length the sex-averaged map length = (female map legnth + male map length)/2.
For species with differentiated sex chromosomes (XY,ZW,XO, a.k.a heterogametic): sex-averaged = sum of sex-averaged autosomes ((female map legnth + male map length)/2) + the length of the map for the homogemetic sex chromosome (Z,X). 

## The rate is derived and can be updated

`maps.csv` holds `map_length_cM` and `genome_size_mb`. It does **not** hold a recombination
rate. That is computed in `recombination_rates.csv` by `scripts/build_derived.py`:

    recombination_rate_cM_per_Mb = map_length_cM / genome_size_mb

`rate_as_published_cM_per_Mb` is retained separately: it is what the *source study* printed,
useful for comparison, and it is not what the derived table computes.

CI runs `build_derived.py --check` on every pull request, so a change to a map length or
genome size that is not accompanied by a rebuild fails the build.

## Reproducing the published analysis

    maps[maps.passes_2017_criteria]

The two criteria from the paper are applied per record and stored as flags:

| Flag | Criterion | n |
|---|---|---|
| `qc_few_markers` | fewer than 50 mapped markers | 13 |
| `qc_lg_hcn_mismatch` | \|linkage groups − n\| / n > 0.7 | 23 |
| `qc_duplicate_of_other_record` | same map re-reported in a later compilation | 2 |

**All 353 published records pass, and `in_published_353` matches the supplement exactly.**
Records that fail are kept and flagged — filtered, not deleted — so a future analysis can
choose its own thresholds.

## Composition

| | n |
|---|---|
| Total records | 493 |
| Meeting the 2017 criteria | 400 |
| In the published supplement | 353 |
| Added since the paper | 140 |
| Lacking a reference | 0 |

Every record now carries a `ref_id`. The working file originally had 105 records with no
entry in the published reference list; a 2026 recovery campaign traced 103 of them, and the
two that could not be traced to any source (a *Lateolabrax japonicus* and a *Pinus
sylvestris* record) were removed rather than kept unverifiable — the only exception so far
to the filter-don't-delete rule, made because their provenance, not merely their quality,
was in doubt. Their values remain in `legacy/` and in git history.

## Genome size is a separate table

`genome_sizes.csv` holds one row per estimate per species — 683 estimates covering **447 of
the 459 species**, 219 of them with more than one. Each estimate carries its `method`:

| Method | n | Meaning |
|---|---|---|
| `assembly_or_direct` | 280 | Assembly size or a directly reported value |
| `estimate_unspecified` | 209 | Carried in the compilation with no method recorded |
| `c_value` | 172 | Converted from a C-value |
| `other_literature` | 22 | Present only in the combined column; method not recoverable |

`maps.genome_size_id` names which estimate a given map used, so the choice is explicit and
an estimate can be corrected without touching the map record. `used_in_maps` marks the 450
estimates actually in use; the other 233 are alternatives for species where a different
estimate was preferred, plus the five withheld values described under Known limitations.

**A caveat on C-value conversion.** Where the compilation converted a C-value to Mb, 132 of
181 used the standard 978 Mb/pg. The remaining 49 imply factors from 67 to 1535 — meaning
the Mb value did not come from that C-value by the standard conversion, and the two columns
have different provenance. Those rows keep both `genome_size_mb` and `c_value_pg` so the
discrepancy stays visible.

## Known limitations

1. **11 map records (11 species) have no usable genome size**, so no recombination rate
   can be derived for them: *Amphilophus astorquii*, *Anthurium ornatum*, *Chlamys
   noblis*, *Drosophila mediopunctata*, *Gnathopogon caerulescens*, *Nodipecten
   subnodosus*, *Perisoreus infaustus*, *Populus fremontii*, *Prunus virginiana*,
   *Scophthalmus rhombus* and *Typhula ishikariensis*. A 2026 sweep of current sources
   (NCBI Datasets, the Kew and animal C-value databases, and the literature) found no
   assembly and no published flow-cytometry value for any of them; the three withheld
   unverified compilation values that previously fell in this group (*Pagellus
   erythrinus*, *Picea mariana*, *Ribes nigrum*) have been superseded by verified
   assembly-based estimates and remain in `genome_sizes.csv` flagged and unused.

   Supplying a genome size with its method is the second most valuable contribution after
   supplying a missing reference.
2. **`genome_size_method` is `estimate_unspecified` for 209 estimates** — the compilation
   did not record where they came from.
3. **Genome size is species-level, not study-level.** A map from 2005 may be paired with a
   genome size measured in 2015. Ideally each map would cite the genome size *its authors*
   used; the current data cannot support that.
4. **40 records were taken from Corbett-Detig et al. 2015** rather than the primary study
   (`from_corbett_detig_2015`). Two of these duplicate another row exactly and are flagged.
5. **`map_sex` is `sex_averaged` for most records**, but the source coded two distinct
   values (`y`/`n`) that both mean sex-averaged. Any distinction they carried is lost.
