# `species_traits.csv` — species-level traits

**3,071 observations across 457 species and 23 traits**, 163 with a primary literature citation. Third table in the plan (§3).

## Why this is separate from `species.csv`

Taxonomy and traits answer different questions and have different provenance.

Taxonomy is a **resolved external fact** — one authority (Open Tree of Life), refreshable
by re-running resolution, and applying uniformly to every row. Traits are **observations**:
each has its own source, its own scoring scope, and its own uncertainty. Mixing them makes
the second kind look as authoritative as the first.

The practical consequence is that a trait's *absence* carries meaning that a wide table
cannot express. Leaf phenology is not missing for *Gallus gallus* — it is not applicable.
Haplodiploidy is not missing for *Zea mays*. If these were columns on `species.csv`, the
table would be roughly 70% empty and no user could tell "not applicable" from "not scored"
from "scored as absent". In long format, a row's absence means *not scored*, and
`trait_definitions.scored_for` says which lineages were in scope.

## The three files

| File | Content |
|---|---|
| `species_traits.csv` | The observations: `ott_id`, `species_name`, `trait`, `value`, `value_type`, `source` |
| `trait_definitions.csv` | One row per trait: definition, what it applies to, **what it was actually scored for**, and known caveats |
| `trait_vocabularies.csv` | Allowed values per categorical trait, with definitions |

Join to taxonomy on `species_name` or `ott_id`. To get a wide frame in R:
`tidyr::pivot_wider(traits, names_from = trait, values_from = value)`.

## Scoring scope — read this before analysing

Coverage is strongly lineage-structured, and the structure is a property of **how the data
were compiled**, not of biology:

- `parasitic_or_pathogenic` — scored for all 457 species.
- `habitat` — all free-living species (419). Parasites carry `host_type` instead.
- **`invasive` — scored for ANIMALS ONLY.** All 41 positive records are Metazoa. In the
  source file every plant and fungus carries `n`, but that is an unscored default rather
  than a negative observation: *Cynodon dactylon*, *Lolium perenne*, *Ricinus communis* and
  *Spartina pectinata* are all in the dataset marked `n` despite well-documented invasive
  populations. **Those defaults are omitted here rather than recorded as false** — 182
  animals are scored, 275 non-animals are absent. Treating the original column at face
  value would give a false "invasiveness is confined to animals" result.
- Leaf and growth-form traits — plants only, 69–74% of Chloroplastida.
- `haplodiploid` — animals (92% of Metazoa).
- `sex_determination_karyotype` — best covered in Fungi (77%).

## A field that was two variables

`Habitat` in the source file holds `Terrestrial`/`Aquatic`/`Soil`/`Complex` for free-living
species and `Plants`/`Animals` for parasites — habitat and host type in one column, cleanly
separated by parasitic status (38 of 38 parasites carry a host value; no free-living species
does). These are split into `habitat` and `host_type`, which are mutually exclusive.

## Vocabulary — now fully documented

Every value in `trait_vocabularies.csv` carries a definition. The codes that were opaque in
the source file were supplied by the compiler:

| Trait | Value | Meaning |
|---|---|---|
| `heterochiasmy` | H | Male and female map lengths differ in this species |
| | A | Achiasmy: no crossing over in the heterogametic sex |
| `sex_determination_karyotype` | XY / ZW / XO / UV | Sex-chromosome system |
| | H | Homomorphic — sex chromosomes the same size or undifferentiated |
| `sex_determination_genotypic` | MH / FH | Male heterogametic (as in humans) / female heterogametic (as in birds) |
| `plant_life_form` | P / PA | Perennial / both forms reported |

## Provenance from the Tree of Sex database

`Sex_data/` holds three Tree of Sex datasets — 37,506 species across plants, vertebrates and
invertebrates — each carrying a **per-value source citation**. 100 of our 457 species appear
there.

Two things came of matching them:

**Independent validation.** Where both sources have a value, agreement is exact:
35/35 for `sex_determination_karyotype`, 34/34 for `sex_determination_genotypic`. The
compiled codings hold up.

**Real citations.** 163 trait values now carry a primary literature citation in
`source_citation` (e.g. `Rutkowska J. et al. (2012) Biology Letters 8: 636-638` for the ZW
karyotype of *Gallus gallus*) rather than pointing only at the compilation.
13 further values that the compilation lacked were added from this source.

## A correction

Two species — *Allium cepa* and *Lactuca sativa* — carried `SC` in the genotypic
sex-determination column. `SC` is a **Selfing** value (self-compatible) that had landed in
the wrong column: both are hermaphroditic plants with no sex chromosomes, both had an empty
Selfing field, and every other value in that column is MH or FH in animals. Those two rows
were removed.

## Cross-check against the map data

The heterochiasmy coding is consistent with the sex-specific map lengths recorded in the
source: the single achiasmic species, *Papilio glaucus*, has a female/male map-length ratio
of 0.08. Note that `H` marks any species where the sexes differ, including 13 with ratios
within 5% of parity — it is a qualitative flag, not a magnitude, and analyses of the
*degree* of heterochiasmy should use the map lengths directly.

## Still outstanding

`genus_n_species` and `genus_n_dioecious_species` are **genus-level** attributes recorded
per species; they belong in a genus table rather than here.

The Tree of Sex files carry traits this database does not yet use — molecular basis of sex
determination, environmental sex determination, predicted ploidy, and sex-specific
chromosome counts — for far more species than are currently in the database. They are a
ready source for future trait expansion.

`parasitic_or_pathogenic` and `invasive` agree exactly between `LinkageMapIinfo2.csv` and
the published `SuppDat.csv` for all 353 overlapping species.
