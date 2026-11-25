# The plugin has no icon, so the plugin directory checks warn ICON_MISSING

Status: OPEN · Priority: LOW · Type: packaging · Cost: none

> Found while validating the 2026-11-25 dry-run follow-ups. Not caused by
> them: no icon has ever existed in the repo.

## Symptom

`claude plugin validate --strict .` passes, but its plugin directory checks
print one warning: no `icon` in `.claude-plugin/plugin.json` and no
`.claude-plugin/icon.png` or `assets/icon.png`.

## Evidence

```
$ claude --version
2.1.332 (Claude Code)
$ claude plugin validate --strict .
...
⚠ Found 1 plugin directory warning:
  ❯ .claude-plugin/plugin.json icon: No icon (ICON_MISSING). ...
    Fix: Add a square PNG to the plugin folder at .claude-plugin/icon.png, or set `icon`
    in plugin.json to the path of a square PNG or JPEG in the plugin: 512 to 2048 px on
    each side, under 2 MB. SVG and WebP are not accepted. That file may become the
    listing icon only once: the first time the plugin is saved or submitted in the
    developer portal. Adding or changing it later does not change the icon.
...
✔ Validation passed
exit 0
```

## Why it matters

It does not fail validation or affect installs from this repo's marketplace.
It matters only if the plugin is submitted to the plugin directory: the
validator says the icon is taken once, at the first submission, and cannot be
changed later.

## Scope to decide

- Add a square PNG (512 to 2048 px) at `.claude-plugin/icon.png` before any
  directory submission, chosen by the owner.
- OR leave it until a directory submission is planned.

No code change made by this ticket. It is an observation on the record.
