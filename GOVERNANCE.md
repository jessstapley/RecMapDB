# Governance

## Roles

**Contributors** submit records. Anyone.

**Curators** review and merge submissions, assign `map_id`s, and adjudicate flagged
records. Curators are added by consensus of the existing curators.

**Steering group** decides scope, approves schema changes, and sets authorship policy.

## Schema changes

Any change to a column name, type, or meaning requires: an issue describing the change and
its rationale, a two-week comment period, and a minor version bump. Column names are never
silently repurposed.

## Corrections

Anyone may open an issue against an existing record. Corrections are logged in
`CHANGELOG.md` against the affected `map_id`. A database that visibly corrects itself is
more trustworthy than one that never appears to change.

## Review turnaround

We aim to review submissions within one month.

## Releases

`MAJOR.MINOR.PATCH` on the data: MAJOR = breaking schema change, MINOR = new records,
PATCH = corrections. Each tagged release mints a Zenodo DOI. The concept DOI always
resolves to the latest version.
