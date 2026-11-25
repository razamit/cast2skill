# Heredoc delimiter suffixes are unique within a run but look alike

Status: OPEN · Priority: LOW · Type: robustness · Cost: none

## Symptom

In the independent end-to-end run at b93cbb9 the model picked fresh suffixes
for each heredoc, but they resembled each other: k7Qx2mPd, k7Qm2Lxa,
k7Qm2xRz (runs tB1 to tB4 in the session scratchpad, `e2e2/runs`).

## Evidence

```
k7Qx2mPd
k7Qm2Lxa
k7Qm2xRz
```

Each differs from the others, so none collided. The shared `k7Q` prefix shows
the model is not drawing from a real random source.

## Why it matters

Low risk: a pasted text would have to contain the exact delimiter to end the
heredoc early, and the model also checks the text for it. The weakness is only
that the suffix is model-chosen, not random.

## Scope to decide

- Option A: leave as is.
- OR Option B: have the script hand out a fresh delimiter (for example in the `fetch` result or a `delimiter` command) and have the skill use it.

No code change made by this ticket. It is an observation on the record.
