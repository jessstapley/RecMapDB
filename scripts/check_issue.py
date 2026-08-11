#!/usr/bin/env python3
"""Check a submitted 'Add a linkage map record' issue form.

Run by .github/workflows/check_new_record.yml when such an issue is opened or
edited. Reads the issue body from the GitHub event payload, checks the DOI
against Crossref, the species name against the Open Tree of Life taxonomy, and
the numbers against plausibility ranges, then writes a markdown report that the
workflow posts back as an issue comment.

Checks are advisory: a failed check flags the record for the curator, it does
not reject the submission.
"""
import json
import os
import re
import sys

import requests

UA = {"User-Agent": "RecMapDB-record-check (https://github.com/jessstapley/RecMapDB)"}


def parse_form(body: str) -> dict:
    """GitHub renders an issue form as '### <label>\\n\\n<value>' blocks."""
    fields = {}
    for m in re.finditer(r"###\s+(.+?)\s*\n+((?:(?!###).)*)", body, re.S):
        label = m.group(1).strip()
        value = m.group(2).strip()
        if value in ("_No response_", "None", ""):
            value = None
        fields[label] = value
    return fields


def get_num(fields, label):
    raw = fields.get(label)
    if raw is None:
        return None, None
    cleaned = raw.replace(",", "").replace(" ", "")
    try:
        return float(cleaned), raw
    except ValueError:
        return None, raw


def check_doi(doi):
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi.strip())
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=30)
    except requests.RequestException as e:
        return None, f"Crossref could not be reached ({e.__class__.__name__}); curator should check the DOI by hand."
    if r.status_code != 200:
        return None, f"DOI `{doi}` did not resolve on Crossref (HTTP {r.status_code})."
    msg = r.json()["message"]
    title = (msg.get("title") or ["(no title)"])[0]
    year = None
    for k in ("published-print", "published-online", "issued"):
        parts = msg.get(k, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    journal = (msg.get("container-title") or [""])[0]
    first_author = ""
    if msg.get("author"):
        first_author = msg["author"][0].get("family", "")
    return dict(doi=doi, title=title, year=year, journal=journal, first_author=first_author), None


def check_species(name):
    try:
        r = requests.post(
            "https://api.opentreeoflife.org/v3/tnrs/match_names",
            json={"names": [name], "do_approximate_matching": True},
            headers=UA, timeout=30,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        return None, f"Open Tree of Life could not be reached ({e.__class__.__name__}); curator should resolve the species by hand."
    results = r.json().get("results", [])
    if not results or not results[0].get("matches"):
        return None, f"`{name}` found no match in the Open Tree of Life taxonomy."
    m = results[0]["matches"][0]
    tax = m["taxon"]
    return dict(
        ott_id=tax["ott_id"],
        accepted=tax.get("unique_name") or tax["name"],
        synonym=m.get("is_synonym", False),
        approximate=m.get("is_approximate_match", False),
        score=m.get("score"),
    ), None


def main():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    body = event["issue"]["body"] or ""
    fields = parse_form(body)

    ok, warn, fail = [], [], []

    # --- DOI ---
    doi_raw = fields.get("DOI of the study")
    if not doi_raw:
        fail.append("No DOI supplied.")
    else:
        info, err = check_doi(doi_raw)
        if err:
            (warn if "could not be reached" in err else fail).append(err)
        else:
            ok.append(
                f"DOI resolves: **{info['first_author']} {info['year']}**, "
                f"*{info['title']}*, {info['journal']} (`{info['doi']}`)"
            )

    # --- species ---
    species = fields.get("Species (binomial)")
    if not species:
        fail.append("No species supplied.")
    else:
        info, err = check_species(species)
        if err:
            (warn if "could not be reached" in err else fail).append(err)
        else:
            line = f"Species resolves to **{info['accepted']}** (ott{info['ott_id']})"
            notes = []
            if info["synonym"]:
                notes.append("matched via a synonym")
            if info["approximate"]:
                notes.append("fuzzy match — check the spelling")
            if notes:
                line += " — " + "; ".join(notes)
                warn.append(line)
            else:
                ok.append(line)

    # --- numbers ---
    length, _ = get_num(fields, "Sex-averaged map length (cM)")
    markers, _ = get_num(fields, "Number of mapped markers")
    lg, _ = get_num(fields, "Number of linkage groups")
    hcn, _ = get_num(fields, "Haploid chromosome number (n)")
    gsize, gsize_raw = get_num(fields, "Genome size (Mb)")

    if length is None:
        fail.append("Map length is missing or not a number.")
    elif not (20 <= length <= 20000):
        warn.append(f"Map length {length} cM is outside the plausible range 20–20,000 cM — check the units.")
    else:
        ok.append(f"Map length {length} cM is plausible.")

    if markers is not None and lg is not None:
        if markers < lg:
            fail.append(f"{markers:.0f} markers across {lg:.0f} linkage groups — fewer markers than groups cannot be right.")
        elif markers < 50:
            warn.append(f"Only {markers:.0f} markers — the record will carry the `qc_few_markers` flag.")
        else:
            ok.append(f"{markers:.0f} markers across {lg:.0f} linkage groups.")

    if lg is not None and hcn is not None and hcn > 0:
        ratio = abs(lg - hcn) / hcn
        if ratio > 0.7:
            warn.append(
                f"{lg:.0f} linkage groups vs haploid chromosome number {hcn:.0f} "
                f"(|LG−n|/n = {ratio:.2f} > 0.7) — the record will carry the `qc_lg_hcn_mismatch` flag."
            )
        else:
            ok.append(f"Linkage groups ({lg:.0f}) are consistent with the haploid chromosome number ({hcn:.0f}).")

    if gsize_raw is not None:
        if gsize is None:
            warn.append(f"Genome size `{gsize_raw}` is not a number.")
        elif not (1 <= gsize <= 150000):
            warn.append(f"Genome size {gsize} Mb is outside the plausible range 1–150,000 Mb — check the units (Mb, not Gb or pg).")
        elif length:
            ok.append(f"Derived recombination rate would be **{length / gsize:.3f} cM/Mb**.")

    # --- report ---
    lines = ["## Automated record check", ""]
    if ok:
        lines += [f"- :white_check_mark: {x}" for x in ok]
    if warn:
        lines += [f"- :warning: {x}" for x in warn]
    if fail:
        lines += [f"- :x: {x}" for x in fail]
    lines += ["",
              "These checks are advisory — a curator will review this record before it enters the database. "
              "If something above looks wrong, you can edit your submission (three-dot menu → Edit) and the check will run again."]
    report = "\n".join(lines)
    print(report)
    with open("issue_report.md", "w") as f:
        f.write(report)
    # Advisory: never fail the workflow over data content.
    sys.exit(0)


if __name__ == "__main__":
    main()
