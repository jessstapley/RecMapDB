# `species.csv` — taxa

**457 rows, 45 fields.** One row per distinct species string in the source data. Second of
the seven tables in `docs/recmapdb_plan.md` §3.

## How it was built

Every source species string was resolved against the **Open Tree of Life** taxonomy
(TNRS `match_names`, then `taxon_info` with lineage), and **NCBI Taxonomy** was queried
independently as a cross-check. Source taxonomy columns are retained beside the resolved
values, so every change is auditable rather than silently applied.

All 457 names now resolve: 456 automatically, plus `Pyrus x` handled by hand (see below).

## Coverage

| Field | Populated |
|---|---|
| `ott_id`, `species_name`, `eukaryote_supergroup` | 457 (100%) |
| `ncbi_taxid` | 451 (99%) |
| `genus` | 451 (99%) |
| `family` | 446 (98%) |
| `gbif_id` | 432 (95%) |
| `kingdom` | 444 (97%) |

Composition: Chloroplastida 231, Metazoa 182, Fungi 30, SAR 12, Rhodophyta 1, Discoba 1.

**Use `eukaryote_supergroup`, not `kingdom`, for grouping.** OTT has no kingdom-rank
ancestor for protists and brown algae, so `kingdom` is empty for 13 taxa (*Plasmodium*,
*Phytophthora*, *Ectocarpus*, *Toxoplasma*, *Trypanosoma* and relatives).
`eukaryote_supergroup` is derived from the full lineage and is populated for every row.

## What resolution found

OTT and NCBI agree on family for **97%** of taxa (424/439), on order for 98%. Where they
disagree it is mostly the Amaranthaceae/Chenopodiaceae circumscription — a real
disagreement between authorities, not an error.

**42 stored OTT ids no longer point to the taxon the name resolves to** — these are not
cosmetic:

| Type | n | Example |
|---|---|---|
| Same genus, different species | 21 | *Anthurium ornatum* stored as *A. punctatum* |
| Different taxon | 11 | *Bicyclus anynana* stored as *Mycalesis anynana* |
| Stored id no longer exists | 4 | *Lens culinaris* |
| Stored id was a hybrid | 3 | *Aegilops tauschii* stored as *A. tauschii* × *Secale cereale* |
| Stored id was infraspecific | 3 | *Betula pendula* stored as subsp. *pendula* |

The hybrid cases matter most for the science: a recombination rate attributed to
*Aegilops tauschii*, *Prunus persica* or *Aristichthys nobilis* was keyed to a **hybrid**
taxon id. Whether the underlying map is from the pure species or the cross is worth
checking against the source paper.

**37 source family names differ from OTT.** 21 are spelling errors in the source file
(`Daphtniidae`→Daphniidae, `Halliotidae`→Haliotidae, `Coinidae`→Cionidae,
`Chlamydomoadaceae`→Chlamydomonadaceae). 16 are genuine revisions or errors — the clearest
being *Camellia sinensis* filed under **Brassicaceae** (correct: Theaceae).

**4 rows are 2 duplicate taxa.** *Fenneropenaeus chinensis* / *Penaeus chinensis* and
*Pseudocercospora fijiensis* / *Mycosphaerella fijiensis* are each one organism entered
twice under different names. Their map records should be merged or explicitly treated as
two independent maps of the same species.

**8 records are not at species rank** — six genus-only entries (*Hieracium*, *Quercus*,
*Lilium*, *Lagerstroemia*, *Laupala*, *Triticosecale*), one subspecies, and `Pyrus x`.

**`Pyrus x`** was a placeholder for an unnamed interspecific hybrid. Resolved to the
*genus* Pyrus (ott259068) and flagged; the Chen (2015) source should be consulted to
identify the actual cross.

**1 chromosome-number conflict.** *Cynodon dactylon* has two map records reporting 1n = 9
and 1n = 18 — a polyploid series, not an error. Both `chromosome_number_1n` and `_2n` are
therefore null with `flag_chromosome_conflict` set, because a median across a ploidy series
would be meaningless.

## Keys

`species_name` is the primary key and is unique. **`ott_id` is not unique** — the two
synonym pairs share an id, which is correct and is what `flag_duplicate_taxon` records.
When `maps.csv` is built it should reference `ott_id`, and the duplicate pairs must be
resolved first.

## Files

- `species.csv` — the table
- `species.schema.json` — Frictionless Table Schema; validates clean
- `species_curation_worklist.csv` — the 62 rows needing a human decision
