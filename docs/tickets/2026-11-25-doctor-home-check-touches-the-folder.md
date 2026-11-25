# `doctor`'s home-writable check creates and deletes a file in the cast2skill home

Status: OPEN · Priority: LOW · Type: side effect in a read-only check · Cost: none

## Symptom

`doctor` tests whether the cast2skill home is writable by creating and then
deleting a temp file there. That changes the folder's modification time even
though doctor is meant to be a read-only check. Seen in the independent
end-to-end run at 77e5514.

## Evidence

```
$ ls -ld <cast2skill home>   # before and after `doctor`
(modification time differs after the run)
```

## Why it matters

Minor. Nothing is lost, but anything watching the folder's mtime sees a change
that no real work caused.

## Scope to decide

- Option A: use `os.access(home, os.W_OK)`, which does not touch the folder.
- OR Option B: a different probe that leaves no trace; accept that `os.access` can be wrong on some network or ACL setups.

No code change made by this ticket. It is an observation on the record.
