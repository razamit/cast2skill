# Releases

Every file that carries the version, listed once, and every release cut.
Detected at init or on the first release action; re-detected only by
`/devlog:releases status` or when a listed path no longer exists. The
changelog section for each release is written from the progress entries
stamped with that version.

## Carriers
- Canonical: `.claude-plugin/plugin.json` `version` (planned in `SPEC.md` §5, file not created yet; created at M2)
- Mirrors: none. `.claude-plugin/marketplace.json` carries no version unless a decision row adds one.
- Derived, do not edit: none
- Build number: none
- Tag: `vX.Y.Z`, annotated, latest none (not a git repository yet)
- Changelog style: `## [X.Y.Z] - YYYY-MM-DD`
- Bump policy: decision row 5

## Index, newest first

| Version | Date | Build | Tag → commit | Shipped | Post |
|---|---|---|---|---|---|
