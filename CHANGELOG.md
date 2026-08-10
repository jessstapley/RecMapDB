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
- Reference recovery (2026): the working file had 105 map records with no entry in the
  published reference list. 103 now carry a reference (references.csv 353 → 451 rows;
  484 of 486 maps referenced). Sources: Crossref matching, curator-supplied title lists,
  the Corbett-Detig et al. 2015 supplement, supplied PDFs, and map-statistics matches;
  every recovered row carries `match_confidence = recovered_2026` and a `review_note`
  naming its evidence (audit trail in `docs/references_recovered_2026.csv`).
- Final five recoveries came from curator-supplied PDFs and a map-statistics match:
  Citrus unshiu (Shimada et al. 2014), Populus simonii (Mousavi et al. 2016, male map of
  a paper already in the table), Pseudotsuga menziesii (Ukrainetz et al. 2008, confirming
  the earlier best guess), Vigna subterranea (Ahmad et al. 2016), and Solanum habrochaites
  (Geethanjali et al. 2011, an integrated chromosome-12 map of 16 SSRs spanning 118.7 cM —
  the recorded "12 linkage groups" is evidently a transcription of chromosome 12).
- The last two unreferenced records could not be traced to any source: RM0238
  (Lateolabrax japonicus, "Liu 2016" — no indexed match exists) and RM0351 (Pinus
  sylvestris, "Lind 2007" — the full text of the closest candidate, Yin et al. 2003,
  does not match the recorded statistics; 1468 cM equals a Table 1 genome-length
  estimate and 39 equals the paper's primer-combination count, suggesting a garbled
  transcription that could not be confirmed).

### Removed
- RM0238 and RM0351 (above): removed by curator decision rather than kept, because
  their provenance — not merely their quality — was unverifiable. This is the only
  exception so far to the filter-don't-delete rule; the original values remain in
  `legacy/` and in git history. The Lateolabrax japonicus species and trait rows are
  retained (n_map_records = 0). Pinus sylvestris is re-entered from a verified source
  (see below).

### Added (2026-08-10, curator-supplied papers)
- Nine new map records (RM0487–RM0495) from seven papers, each entered from the full
  text with statistics verified against the PDF, and seven new references
  (`match_confidence = added_2026`):
  - Pinus sylvestris — Yin et al. 2003 (RM0487): the two parental AFLP maps
    (female 188 markers / 12 LG / 1695.5 cM; male 245 / 15 / 1718.5), stored as
    map_length_cM = 1707.0 (mean of the parents) with sex-specific lengths. Replaces
    the removed RM0351.
  - Argyrosomus japonicus — Jackson & Rhode 2024 (RM0488): integrated map, 3992 SNPs,
    24 LG, 2550.5 cM, three families (n = 212). New species (ott415181).
  - Cyprinus carpio — Peng et al. 2016 (RM0489): consensus map, 28,194 SNPs on 14,146
    loci, 50 LG, 10,595.94 cM.
  - Takifugu rubripes — Liu et al. 2022 (RM0490): consensus map, 4416 bin markers,
    22 LG, 3147.8 cM.
  - Populus deltoides / P. simonii — Tong et al. 2020 (RM0491 female map, RM0492 male
    map), following the one-record-per-parent-species precedent set by Mousavi et al.
  - Vigna subterranea — Gao et al. 2022 (RM0493): 234 DArTseq SNPs, 11 LG, 1040.92 cM.
  - Citrus sinensis ('Pêra') and Citrus reticulata ('Murcott' tangor) — Oliveira et al.
    2007 (RM0494, RM0495): one record per parent variety. New species Citrus
    reticulata (ott37136).
- Schema updates: `references.schema.json` year maximum raised 2018 → 2026 and
  `match_confidence` gains `added_2026` for post-2017 additions that were never part
  of the recovery backlog.
- Genome sizes supplied by the curator for the two new species: Argyrosomus japonicus
  673.7 Mb (Zhao et al. 2021 chromosome-level assembly, doi:10.1093/gbe/evaa246;
  GS0638) and Citrus reticulata 347 Mb (wild mandarin v1.0 assembly, Citrus Genome
  Database Analysis/89; GS0639). Both linked to their maps (RM0488, RM0495); the
  derived table gains their rates (435 -> 437 rows; 3.79 and 4.76 cM/Mb).
- Genome sizes recovered from the NCBI eukaryote genome list
  (`legacy/NCBI_eukaryotes_genome_size.txt`) for 10 of the 55 species that lacked one:
  Cervus elaphus, Citrus unshiu, Dendrobium officinale (listed by NCBI as its synonym
  D. catenatum), Haliotis rubra, Mustela vison (listed as Neovison vison),
  Mycosphaerella fijiensis, Philomachus pugnax (listed as Calidris pugnax), Pungitius
  pungitius, Pyrus x (the P. x bretschneideri reference assembly, applied to the
  genus-level hybrid record with a note) and Sebastes schlegelii (GS0640–GS0649, all
  assembly_or_direct, each naming its GCA accession; selection rule chromosome >
  scaffold > contig, then most recent). Citrus unshiu and Mycosphaerella fijiensis
  thereby move off the withheld-unverified list. Derived table 437 -> 447 rows; the
  remaining 46 rate-less records span 42 species with no estimate anywhere and 3 with
  only a withheld unverified value.
