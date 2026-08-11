#!/usr/bin/env python3
"""Turn an 'Add a linkage map record' issue into database rows.

Usage (from the repository root):

    python scripts/issue_to_new_record.py 12              # preview rows for issue #12
    python scripts/issue_to_new_record.py 12 --apply      # append rows, rebuild, validate
    python scripts/issue_to_new_record.py --body-file b.md --issue 12   # offline: body saved to a file

Reads the issue from the GitHub API (no token needed for a public repository;
set GITHUB_TOKEN to raise the rate limit), parses the form, resolves the DOI
against Crossref and the species against the Open Tree of Life, and builds:

  - a references.csv row (unless the DOI is already present, in which case the
    existing ref_id is reused),
  - a species.csv row (only if the species is new; lineage from OTT, source ids
    from its tax_sources; the curator should review it),
  - a genome_sizes.csv row (only if a genome size was supplied),
  - the maps.csv row, with quality flags computed exactly as documented in
    docs/maps_README.md.

Without --apply nothing is written: the rows are printed for review. With
--apply the rows are appended, n_map_records is updated,
scripts/build_derived.py and scripts/validate.py are run, and a suggested
commit message is printed. The curator remains responsible for reviewing the
result and committing.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_issue import parse_form  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = os.environ.get("RECMAPDB_REPO", "jessstapley/RecMapDB")
UA = {"User-Agent": f"recmapdb-curation (https://github.com/{REPO})"}

GS_METHOD = {  # issue-form vocabulary -> genome_sizes.csv vocabulary
    "assembly": "assembly_or_direct",
    "flow_cytometry": "c_value",
    "c_value": "c_value",
    "feulgen_densitometry": "c_value",
    "other": "estimate_unspecified",
    "unknown": "estimate_unspecified",
}
RANKS = ("kingdom", "phylum", "class", "order", "family", "genus")


def die(msg):
    sys.exit(f"ERROR: {msg}")


def fetch_issue(number):
    headers = dict(UA)
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    r = requests.get(f"https://api.github.com/repos/{REPO}/issues/{number}",
                     headers=headers, timeout=30)
    if r.status_code != 200:
        die(f"could not fetch issue #{number} (HTTP {r.status_code}); "
            "use --body-file to work from a saved copy of the issue body")
    j = r.json()
    return j["body"] or "", j["user"]["login"]


def crossref(doi):
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi.strip()).lower()
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=30)
    except requests.RequestException as e:
        die(f"could not reach Crossref ({e.__class__.__name__}) — check the network and retry")
    if r.status_code != 200:
        die(f"DOI {doi} did not resolve on Crossref (HTTP {r.status_code})")
    m = r.json()["message"]
    year = None
    for k in ("published-print", "published-online", "issued"):
        parts = m.get(k, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    authors = "; ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
                        for a in m.get("author", []))
    first = (m.get("author") or [{}])[0].get("family", "anon")
    return dict(
        doi=doi, year=year, authors=authors, first_author=first,
        title=(m.get("title") or [""])[0],
        journal=(m.get("container-title") or [""])[0],
        volume=m.get("volume", ""), issue=m.get("issue", ""),
        pages=m.get("page", ""), publisher=m.get("publisher", ""),
        issn=(m.get("ISSN") or [""])[0],
    )


def ott_resolve(name):
    try:
        r = requests.post("https://api.opentreeoflife.org/v3/tnrs/match_names",
                          json={"names": [name]}, headers=UA, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        die(f"could not reach the Open Tree of Life API ({e.__class__.__name__}) — check the network and retry")
    results = r.json().get("results", [])
    if not results or not results[0].get("matches"):
        die(f"species '{name}' not found in the Open Tree of Life taxonomy; "
            "strip strain/cultivar information and use the plain binomial")
    m = results[0]["matches"][0]
    tax = m["taxon"]
    info = requests.post("https://api.opentreeoflife.org/v3/taxonomy/taxon_info",
                         json={"ott_id": tax["ott_id"], "include_lineage": True},
                         headers=UA, timeout=30).json()
    lineage = info.get("lineage", [])
    by_rank = {t["rank"]: t["name"] for t in lineage if t.get("rank") in RANKS}
    sources = {}
    for s in info.get("tax_sources", []):
        k, _, v = s.partition(":")
        sources[k] = v
    return dict(
        ott_id=f"ott{tax['ott_id']}",
        accepted=tax.get("unique_name") or tax["name"],
        rank=tax.get("rank", "species"),
        synonym=m.get("is_synonym", False),
        by_rank=by_rank,
        full_lineage="; ".join(t["name"] for t in lineage),
        ncbi=sources.get("ncbi", ""), gbif=sources.get("gbif", ""),
        irmng=sources.get("irmng", ""),
    )


def slug(surname):
    s = unicodedata.normalize("NFKD", surname).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower()) or "anon"


def load(path):
    with path.open(newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def append(path, fields, new_rows):
    _, rows = load(path)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows + new_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("number", nargs="?", type=int, help="issue number")
    ap.add_argument("--body-file", help="file holding a saved copy of the issue body")
    ap.add_argument("--issue", type=int, help="issue number when using --body-file")
    ap.add_argument("--apply", action="store_true", help="append rows, rebuild, validate")
    args = ap.parse_args()

    if args.body_file:
        body = Path(args.body_file).read_text()
        number, submitter = args.issue or 0, "(offline)"
    elif args.number:
        number = args.number
        body, submitter = fetch_issue(number)
    else:
        ap.error("give an issue number, or --body-file with --issue")

    f = parse_form(body)
    doi = f.get("DOI of the study") or die("no DOI in the form")
    species_raw = f.get("Species (binomial)") or die("no species in the form")

    def num(label):
        v = f.get(label)
        if v is None:
            return None
        try:
            return float(v.replace(",", ""))
        except ValueError:
            die(f"'{label}' is not a number: {v!r}")

    length = num("Sex-averaged map length (cM)") or die("no map length")
    markers = num("Number of mapped markers")
    lg = num("Number of linkage groups")
    hcn = num("Haploid chromosome number (n)")
    pop_n = num("Number of individuals in the mapping population")
    gsize = num("Genome size (Mb)")
    map_sex = (f.get("Which map is this?") or "sex_averaged").strip()
    if map_sex == "unknown":
        print("NOTE: map_sex 'unknown' stored as 'sex_averaged' (schema vocabulary).")
        map_sex = "sex_averaged"

    ref = crossref(doi)
    sp = ott_resolve(species_raw)
    species_name = sp["accepted"]
    if species_name != species_raw:
        print(f"NOTE: '{species_raw}' resolved to accepted name '{species_name}'.")

    rfields, refs = load(DATA / "references.csv")
    sfields, spdb = load(DATA / "species.csv")
    mfields, maps = load(DATA / "maps.csv")
    gfields, gsdb = load(DATA / "genome_sizes.csv")

    new_refs, new_species, new_gs = [], [], []

    # ---- reference ----
    existing = {r["doi"].lower(): r["ref_id"] for r in refs if r["doi"]}
    if ref["doi"] in existing:
        ref_id = existing[ref["doi"]]
        print(f"Reference already present as {ref_id}; reusing it.")
    else:
        base = f"{slug(ref['first_author'])}{ref['year']}"
        taken = {r["ref_id"] for r in refs}
        ref_id = base
        for suffix in "abcdefgh":
            if ref_id not in taken:
                break
            ref_id = base + suffix
        row = {k: "" for k in rfields}
        row.update(ref_id=ref_id, doi=ref["doi"], authors=ref["authors"],
                   year=str(ref["year"]), title=ref["title"], journal=ref["journal"],
                   journal_normalized=ref["journal"], volume=ref["volume"],
                   issue=ref["issue"], pages=ref["pages"], publisher=ref["publisher"],
                   issn=ref["issn"], match_confidence="added_2026",
                   manual_review="accept",
                   review_note=f"Community submission via issue #{number} (@{submitter}); "
                               "DOI resolved against Crossref by scripts/issue_to_new_record.py.",
                   flag_year_mismatch="False", flag_author_list_incomplete="False",
                   flag_no_doi="False")
        new_refs.append(row)

    # ---- species ----
    known = {r["species_name"]: r["ott_id"] for r in spdb}
    if species_name in known:
        ott_id = known[species_name]
    else:
        ott_id = sp["ott_id"]
        if any(r["ott_id"] == ott_id for r in spdb):
            die(f"{ott_id} already in species.csv under a different name — resolve by hand")
        row = {k: "" for k in sfields}
        row.update(ott_id=ott_id, species_name=species_name,
                   ott_accepted_name=species_name, ott_unique_name=species_name,
                   taxon_rank=sp["rank"],
                   kingdom=sp["by_rank"].get("kingdom", ""),
                   phylum=sp["by_rank"].get("phylum", ""),
                   **{"class": sp["by_rank"].get("class", "")},
                   order=sp["by_rank"].get("order", ""),
                   family=sp["by_rank"].get("family", ""),
                   genus=sp["by_rank"].get("genus", ""),
                   full_lineage=sp["full_lineage"],
                   ncbi_taxid=sp["ncbi"], gbif_id=sp["gbif"], irmng_id=sp["irmng"],
                   chromosome_number_1n=("" if hcn is None else f"{hcn:g}"),
                   chromosome_number_2n=("" if hcn is None else f"{hcn * 2:g}"),
                   flag_chromosome_conflict="False", n_map_records="0",
                   ott_match_score="1.0", flag_ott_id_changed="False",
                   flag_name_is_synonym=str(sp["synonym"]),
                   flag_fuzzy_match="False",
                   flag_not_species_rank=str(sp["rank"] != "species"),
                   flag_unresolved="False", flag_source_family_differs="False",
                   flag_duplicate_taxon="False")
        new_species.append(row)
        print(f"NEW SPECIES row for {species_name} ({ott_id}) — review lineage and NCBI cross-check.")

    # ---- genome size ----
    gs_id = gs_mb = gs_method = ""
    if gsize is not None:
        gs_method = GS_METHOD.get(f.get("How was genome size estimated?") or "unknown",
                                  "estimate_unspecified")
        last = max(int(r["genome_size_id"][2:]) for r in gsdb)
        gs_id = f"GS{last + 1:04d}"
        gs_mb = f"{gsize:g}"
        src = f.get("Source of the genome size") or f.get("Genome assembly accession") \
              or f"community submission, issue #{number}"
        row = {k: "" for k in gfields}
        row.update(genome_size_id=gs_id, ott_id=ott_id, species_name=species_name,
                   genome_size_mb=gs_mb, method=gs_method, source=src,
                   note=f"Supplied via issue #{number}.",
                   used_in_maps="True", flag_unverified="False")
        new_gs.append(row)

    # ---- map record ----
    last = max(int(r["map_id"][2:]) for r in maps)
    map_id = f"RM{last + 1:04d}"
    few = "True" if (markers is not None and markers < 50) else "False"
    mism = "True" if (lg is not None and hcn and abs(lg - hcn) / hcn > 0.7) else "False"
    passes = "True" if (few == "False" and mism == "False") else "False"
    mrow = {k: "" for k in mfields}
    mrow.update(map_id=map_id, ott_id=ott_id, species_name=species_name, ref_id=ref_id,
                map_length_cM=f"{length:g}", map_sex=map_sex,
                n_markers=("" if markers is None else f"{markers:g}"),
                n_linkage_groups=("" if lg is None else f"{lg:g}"),
                haploid_chromosome_number=("" if hcn is None else f"{hcn:g}"),
                mapping_population_n=("" if pop_n is None else f"{pop_n:g}"),
                genome_size_mb=gs_mb, genome_size_id=gs_id, genome_size_method=gs_method,
                qc_few_markers=few, qc_lg_hcn_mismatch=mism,
                qc_duplicate_of_other_record="False", passes_2017_criteria=passes,
                in_published_353="False", from_corbett_detig_2015="False",
                needs_reference="False", source_first_author=ref["first_author"],
                source_year=str(ref["year"]))

    for label in ("Cross type", "Predominant marker type", "Mapping software", "Notes"):
        if f.get(label):
            print(f"NOT STORED (no column): {label} = {f[label]} — keep in the issue record.")

    print("\n--- rows to add ---")
    for name, rows in (("references.csv", new_refs), ("species.csv", new_species),
                       ("genome_sizes.csv", new_gs), ("maps.csv", [mrow])):
        for r in rows:
            print(f"[{name}] " + ",".join(str(r[k]) for k in list(r)[:8]) + ",…")

    if not args.apply:
        print("\nPreview only — run again with --apply to write.")
        return

    append(DATA / "references.csv", rfields, new_refs)
    append(DATA / "genome_sizes.csv", gfields, new_gs)
    _, spdb = load(DATA / "species.csv")
    spdb += new_species
    counts = {}
    for r in maps + [mrow]:
        counts[r["species_name"]] = counts.get(r["species_name"], 0) + 1
    for r in spdb:
        r["n_map_records"] = str(counts.get(r["species_name"], 0))
    with (DATA / "species.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=sfields)
        w.writeheader()
        w.writerows(spdb)
    append(DATA / "maps.csv", mfields, [mrow])

    for script in ("build_derived.py", "validate.py"):
        print(f"\n>> {script}")
        rc = subprocess.run([sys.executable, str(ROOT / "scripts" / script)]).returncode
        if rc != 0:
            die(f"{script} failed — fix before committing")

    print(f'\nSuggested commit message:\n  Add {map_id} {species_name} from #{number}'
          f' (submitted by @{submitter})')


if __name__ == "__main__":
    main()
