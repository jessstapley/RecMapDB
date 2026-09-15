#!/usr/bin/env python3
"""Write the author list in .zenodo.json from data/contributors.csv.

Zenodo reads .zenodo.json when it archives a GitHub release, so this script is
what makes the promise in CONTRIBUTING.md mechanical: contribute a record, get a
row in contributors.csv, appear as an author on the next citable release.

    python scripts/make_zenodo_metadata.py            # show what would change
    python scripts/make_zenodo_metadata.py --write    # update .zenodo.json

Only the "creators" key is touched. Everything else in .zenodo.json (title,
licence, description, related identifiers) is hand-maintained and preserved.

Order: maintainers first, then curators, then contributors; alphabetical by
contributor_id within each group, so the list is stable across releases and a
new contributor never silently displaces someone.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRIBUTORS = ROOT / "data" / "contributors.csv"
ZENODO = ROOT / ".zenodo.json"
ROLE_ORDER = {"maintainer": 0, "curator": 1, "contributor": 2}


def truthy(v):
    return str(v).strip().lower() in ("true", "1", "yes", "y", "")


def build_creators():
    with CONTRIBUTORS.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if truthy(r.get("include_in_zenodo_authors"))]
    rows.sort(key=lambda r: (ROLE_ORDER.get((r.get("role") or "").strip(), 3),
                             r["contributor_id"]))
    creators = []
    for r in rows:
        c = {"name": r["name"].strip()}
        if (r.get("affiliation") or "").strip():
            c["affiliation"] = r["affiliation"].strip()
        if (r.get("orcid") or "").strip():
            c["orcid"] = r["orcid"].strip()
        creators.append(c)
    return creators


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="update .zenodo.json in place")
    args = ap.parse_args()

    meta = json.loads(ZENODO.read_text(encoding="utf-8"))
    new = build_creators()
    if not new:
        sys.exit("ERROR: no contributors marked for the author list — refusing to empty it")

    if meta.get("creators") == new:
        print(f".zenodo.json already lists these {len(new)} author(s); nothing to do.")
        return

    print(f"creators: {len(meta.get('creators', []))} -> {len(new)}")
    for c in new:
        print(f"  {c['name']}" + (f"  ({c['orcid']})" if "orcid" in c else ""))
    if not args.write:
        print("\nPreview only — run again with --write to update .zenodo.json.")
        return

    meta["creators"] = new
    ZENODO.write_text(json.dumps(meta, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n.zenodo.json updated.")


if __name__ == "__main__":
    main()
