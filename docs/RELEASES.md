# Releases

Every file that carries the version, listed once, and every release cut.
Detected at init or on the first release action; re-detected only by
`/devlog:releases status` or when a listed path no longer exists. The
changelog section for each release is written from the progress entries
stamped with that version.

## Carriers
- Canonical: `.claude-plugin/plugin.json` `version`
- Mirrors: none. `.claude-plugin/marketplace.json` carries no version unless a decision row adds one.
- Derived, do not edit: none
- Build number: none
- Tag: `vX.Y.Z`, annotated, latest `v0.1.0`
- Changelog style: `## [X.Y.Z] - YYYY-MM-DD`
- Bump policy: decision row 5

## Index, newest first

| Version | Date | Build | Tag → commit | Shipped | Post |
|---|---|---|---|---|---|
| 0.1.0 | 2026-11-25 | none | v0.1.0 → 337bd80 | 2026-11-25, 2026-11-11 | none |
