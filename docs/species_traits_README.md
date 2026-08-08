# `species_traits.csv` — species-level traits

**3,060 observations across 457 species and 23 traits.** Third table in the plan (§3).

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

## Outstanding for the curator

**8 vocabulary values remain undocumented** because the source coding is opaque
(`needs_definition = TRUE` in `trait_vocabularies.csv`):

| Trait | Values | Question |
|---|---|---|
| `heterochiasmy` | H (64), A (11) | Heterochiasmy / achiasmy? |
| `sex_determination_karyotype` | H (55) | Homomorphic? Hermaphrodite? |
| `sex_determination_genotypic` | MH (45), FH (22), SC (2) | Male/female heterogamety, and SC? |
| `plant_life_form` | P (16), PA (3) | Perennial, perennial/annual? |

`genus_n_species` and `genus_n_dioecious_species` are **genus-level** attributes recorded
per species; they belong in a genus table rather than here.

`parasitic_or_pathogenic` and `invasive` agree exactly between `LinkageMapIinfo2.csv` and
the published `SuppDat.csv` for all 353 overlapping species.
