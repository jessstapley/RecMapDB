# Curator guide: turning a submission into database rows

A submitted issue form does not change the database by itself — it is a
structured request. A curator turns it into rows, commits, and closes the
issue. The steps, for a typical single-map submission:

1. **Read the automated check comment** on the issue. It resolves the DOI
   against Crossref, the species against the Open Tree of Life, and
   range-checks the numbers. Green ticks are not a guarantee, but red
   crosses always need resolving with the submitter before going further.

2. **Reference.** If the DOI is not already in `data/references.csv`, add a
   row: `ref_id` is lowercase first-author surname + year (letter-suffixed on
   collision), metadata from Crossref, `match_confidence = added_2026` (or
   the current year's value), `manual_review = accept`, and a `review_note`
   saying the record came from a community submission (cite the issue
   number).

3. **Species.** If the species is not in `data/species.csv`, add a row with
   the OTT id from the check comment, the NCBI taxid, lineage fields copied
   from a congener where available, and `n_map_records` set. Update
   `n_map_records` for existing species.

4. **Map record.** Add a row to `data/maps.csv` with the next free `map_id`
   (RM####). Compute the quality flags exactly as documented in
   `docs/maps_README.md`: `qc_few_markers` (< 50 markers),
   `qc_lg_hcn_mismatch` (|LG − n|/n > 0.7). `in_published_353 = False`,
   `needs_reference = False`, `passes_2017_criteria` from the flags.

5. **Genome size.** If supplied (or findable), add a row to
   `data/genome_sizes.csv` with the next `GS####` id, the method, and a
   source that names an assembly accession, C-value source, or DOI; link it
   from the map row (`genome_size_id`, `genome_size_mb`,
   `genome_size_method`). No genome size means no derived rate — that is
   fine.

6. **Rebuild and validate.**

       python scripts/build_derived.py
       python scripts/validate.py

   Both must pass; CI runs the same checks on the push.

7. **Credit.** Add the submitter to `data/contributors.csv` (name, ORCID,
   issue number) unless they decline.

8. **Commit and close.** Commit with a message that names the map_id, the
   species, and the issue (`Add RM0496 Daphnia magna from #12`). Push, then
   close the issue with a comment linking the commit. GitHub links the two
   automatically if the commit message contains `#<issue number>`.

Batch submissions (pull requests, emailed spreadsheets) follow the same
steps 2–8 per record; the PR route runs validation automatically and posts
the report on the PR.
