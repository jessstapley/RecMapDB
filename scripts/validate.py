#!/usr/bin/env python3
"""Validate recmapdb tables against their Frictionless Table Schemas.

Runs in CI on every pull request, and locally with:  python scripts/validate.py
Exit code 1 if any BLOCKER is found; warnings do not fail the build.
"""
import json, sys, argparse, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TYPE_CHECK = {
    "integer": lambda s: pd.to_numeric(s, errors="coerce").notna() | s.isna(),
    "number":  lambda s: pd.to_numeric(s, errors="coerce").notna() | s.isna(),
    "year":    lambda s: pd.to_numeric(s, errors="coerce").notna() | s.isna(),
    "boolean": lambda s: s.isin([True, False, "True", "False", "true", "false"]) | s.isna(),
}


def validate_table(schema_path):
    schema = json.loads(schema_path.read_text())
    csv_path = DATA / schema["path"]
    blockers, warnings = [], []

    if not csv_path.exists():
        return [f"{schema['path']}: file not found"], []

    df = pd.read_csv(csv_path)
    fields = schema["schema"]["fields"]
    declared = [f["name"] for f in fields]

    missing = [c for c in declared if c not in df.columns]
    extra = [c for c in df.columns if c not in declared]
    if missing:
        blockers.append(f"{schema['path']}: columns in schema but not in CSV: {missing}")
    if extra:
        blockers.append(f"{schema['path']}: columns in CSV but not in schema: {extra}")
    if missing or extra:
        return blockers, warnings

    if declared != list(df.columns):
        warnings.append(f"{schema['path']}: column order differs from schema")

    for f in fields:
        name, ftype = f["name"], f.get("type", "string")
        col, con = df[name], f.get("constraints", {})

        if ftype in TYPE_CHECK:
            bad = ~TYPE_CHECK[ftype](col)
            if bad.any():
                blockers.append(f"{schema['path']}.{name}: {int(bad.sum())} values are not valid {ftype}")

        if con.get("required") and col.isna().any():
            blockers.append(f"{schema['path']}.{name}: {int(col.isna().sum())} missing values in a required field")

        if con.get("unique") and not col.dropna().is_unique:
            n = int(col.dropna().duplicated().sum())
            blockers.append(f"{schema['path']}.{name}: {n} duplicate values in a unique field")

        if "pattern" in con:
            bad = ~col.dropna().astype(str).str.match(con["pattern"])
            if bad.any():
                blockers.append(f"{schema['path']}.{name}: {int(bad.sum())} values fail pattern {con['pattern']}")

        if "enum" in con:
            outside = set(col.dropna().astype(str)) - set(map(str, con["enum"]))
            if outside:
                blockers.append(f"{schema['path']}.{name}: values outside the allowed set: {sorted(outside)[:5]}")

        for bound, op in (("minimum", "<"), ("maximum", ">")):
            if bound in con:
                num = pd.to_numeric(col, errors="coerce")
                bad = num.lt(con[bound]) if op == "<" else num.gt(con[bound])
                if bad.any():
                    blockers.append(f"{schema['path']}.{name}: {int(bad.sum())} values {op} {con[bound]}")

    return blockers, warnings


def trait_checks():
    """Traits: vocabulary, referential integrity, duplicates."""
    blockers, warnings = [], []
    # traits: values must come from the controlled vocabulary
    tr_path = DATA / "species_traits.csv"
    if tr_path.exists():
        tr = pd.read_csv(tr_path)
        spp_names = set(pd.read_csv(DATA / "species.csv").species_name)
        vocab = pd.read_csv(DATA / "trait_vocabularies.csv")
        defs = pd.read_csv(DATA / "trait_definitions.csv")

        orphan = set(tr.species_name) - spp_names
        if orphan:
            blockers.append(f"species_traits.csv: {len(orphan)} species not in species.csv")

        undefined = set(tr.trait) - set(defs.trait)
        if undefined:
            blockers.append(f"species_traits.csv: traits missing from trait_definitions.csv: {sorted(undefined)}")

        cat = tr[tr.value_type.isin(["categorical", "boolean"])]
        allowed = set(zip(vocab.trait, vocab.value))
        bad = {(t, v) for t, v in zip(cat.trait, cat.value)} - allowed
        if bad:
            blockers.append(f"species_traits.csv: {len(bad)} values outside the vocabulary, e.g. {sorted(bad)[:3]}")

        num = tr[tr.value_type == "numeric"]
        if pd.to_numeric(num.value, errors="coerce").isna().any():
            n = int(pd.to_numeric(num.value, errors="coerce").isna().sum())
            blockers.append(f"species_traits.csv: {n} non-numeric values in numeric traits")

        if tr.duplicated(["species_name", "trait"]).any():
            n = int(tr.duplicated(["species_name", "trait"]).sum())
            blockers.append(f"species_traits.csv: {n} duplicate species x trait rows")

        n_undef = int(vocab.needs_definition.sum()) if "needs_definition" in vocab else 0
        if n_undef:
            warnings.append(f"trait_vocabularies.csv: {n_undef} values still lack a definition")

    return blockers, warnings


def cross_table_checks():
    """Referential integrity between tables. Extend as new tables land."""
    blockers, warnings = [], []
    maps_path = DATA / "maps.csv"
    if not maps_path.exists():
        warnings.append("maps.csv not present yet — map referential checks skipped")
        return blockers, warnings

    maps = pd.read_csv(maps_path)
    refs = pd.read_csv(DATA / "references.csv")
    spp = pd.read_csv(DATA / "species.csv")

    orphan_refs = set(maps.ref_id.dropna()) - set(refs.ref_id)
    if orphan_refs:
        blockers.append(f"maps.csv: {len(orphan_refs)} ref_id values not in references.csv")

    orphan_spp = set(maps.ott_id.dropna()) - set(spp.ott_id)
    if orphan_spp:
        blockers.append(f"maps.csv: {len(orphan_spp)} ott_id values not in species.csv")

    # plausibility — these catch unit confusion, the most common real error
    if "map_length_cM" in maps:
        n = int((~maps.map_length_cM.between(20, 20000)).sum())
        if n:
            warnings.append(f"maps.csv: {n} map lengths outside 20-20000 cM — check units")
    if {"n_markers", "n_linkage_groups"} <= set(maps.columns):
        n = int((maps.n_markers < maps.n_linkage_groups).sum())
        if n:
            blockers.append(f"maps.csv: {n} records have fewer markers than linkage groups")

    return blockers, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", help="write a markdown report to this path")
    args = ap.parse_args()

    all_blockers, all_warnings, checked = [], [], []
    for schema_path in sorted(DATA.glob("*.schema.json")):
        b, w = validate_table(schema_path)
        all_blockers += b
        all_warnings += w
        checked.append(schema_path.name.replace(".schema.json", ""))

    for check in (trait_checks, cross_table_checks):
        b, w = check()
        all_blockers += b
        all_warnings += w

    lines = ["## Data validation", ""]
    lines.append(f"Tables checked: {', '.join(checked) or 'none'}")
    lines.append("")
    if all_blockers:
        lines.append(f"### Blockers ({len(all_blockers)})")
        lines += [f"- {x}" for x in all_blockers]
        lines.append("")
    if all_warnings:
        lines.append(f"### Warnings ({len(all_warnings)})")
        lines += [f"- {x}" for x in all_warnings]
        lines.append("")
    if not all_blockers and not all_warnings:
        lines.append("All checks passed.")

    report = "\n".join(lines)
    print(report)
    if args.report:
        Path(args.report).write_text(report)

    sys.exit(1 if all_blockers else 0)


if __name__ == "__main__":
    main()
