#!/usr/bin/env python3
"""Rebuild derived tables from the primary tables.

Derived files are never hand-edited: they are a pure function of data/maps.csv and
data/genome_sizes.csv. Run after any change to those, and in CI to check the committed
derived table matches what the primary tables imply.

    python scripts/build_derived.py            # rebuild
    python scripts/build_derived.py --check    # verify without writing (exit 1 on drift)
"""
import argparse, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def build():
    maps = pd.read_csv(DATA / "maps.csv")

    rr = maps[[
        "map_id", "ott_id", "species_name", "ref_id", "map_length_cM", "genome_size_mb",
        "genome_size_method", "map_sex", "n_markers", "n_linkage_groups",
        "haploid_chromosome_number", "passes_2017_criteria", "in_published_353",
    ]].copy()

    # The headline quantity. Computed here, never stored in maps.csv, so that a corrected
    # genome size or map length propagates automatically.
    rr["recombination_rate_cM_per_Mb"] = (rr.map_length_cM / rr.genome_size_mb).round(6)
    rr["map_length_per_chromosome_cM"] = (rr.map_length_cM / rr.haploid_chromosome_number).round(3)
    rr["marker_interval_cM"] = (rr.map_length_cM / rr.n_markers).round(4)
    rr["fm_map_length_ratio"] = (maps.map_length_female_cM / maps.map_length_male_cM).round(4)

    rr = rr[rr.recombination_rate_cM_per_Mb.notna()].reset_index(drop=True)
    return rr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="compare against the committed file instead of writing")
    args = ap.parse_args()

    rr = build()
    out = DATA / "recombination_rates.csv"

    if args.check:
        if not out.exists():
            print("recombination_rates.csv is missing — run without --check to build it")
            sys.exit(1)
        committed = pd.read_csv(out)
        if len(committed) != len(rr):
            print(f"DRIFT: committed has {len(committed)} rows, rebuild gives {len(rr)}")
            sys.exit(1)
        merged = committed[["map_id", "recombination_rate_cM_per_Mb"]].merge(
            rr[["map_id", "recombination_rate_cM_per_Mb"]], on="map_id", suffixes=("_committed", "_rebuilt"))
        diff = (merged.recombination_rate_cM_per_Mb_committed
                - merged.recombination_rate_cM_per_Mb_rebuilt).abs()
        n = int((diff > 1e-6).sum())
        if n:
            print(f"DRIFT: {n} rates differ from a fresh rebuild")
            sys.exit(1)
        print(f"recombination_rates.csv is up to date ({len(rr)} rows)")
        return

    rr.to_csv(out, index=False)
    n_ok = int((rr.passes_2017_criteria == True).sum())
    print(f"wrote {out.relative_to(ROOT)}: {len(rr)} rows, {n_ok} meeting the 2017 criteria")


if __name__ == "__main__":
    main()
