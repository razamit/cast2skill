"""`check`: a mechanical backstop for SPEC section 10, rule 2.

A lesson that will be written as a skill or a CLAUDE.md rule steers future
sessions, and its words may come from an untrusted transcript. This scans the
text for what such a lesson must never tell the agent to do: run a command,
fetch a URL, install something, change permissions, skip confirmations, hide
information from the user, or contact anyone.

It is strict on purpose and flags some harmless text. Passing it does not
clear a lesson: the rule in SKILL.md still applies. Text is NFKC-normalized
first (fullwidth letters), and words mixing Latin with Cyrillic or Greek
letters are flagged (lookalike spellings of commands).

The only exemption: URLs inside a single trailing `## Source` section of at
most two lines, and inside a one-line `<!-- cast2skill: ... -->` comment.
Everything else in those places is still scanned.
"""

import re
import unicodedata

URL = r"\b(?:https?|ftp|file)://\S+|\bwww\.\S+"
# `make` and `eval` are everyday English ("make sure", "make them pass", "write
# an eval"), so they are flagged only in a command shape: in inline code, after
# a `$ ` prompt or `&&`/`||` (not `;`, as in "small; make sure"), with flags or
# VAR=value, before a target that is never English after "make", or before an
# English-looking target that ends the clause ("then run make test.").
# See DECISIONS.md row 32.
MAKE_TARGETS_ALWAYS = r"install|uninstall|deploy|dist|distclean|lint|bootstrap|publish"
MAKE_TARGETS_AT_CLAUSE_END = r"all|build|check|clean|dev|docs|format|release|run|setup|test|tests"
MAKE_COMMAND = (r"`\s*make\b|(?:\$|&&|\|\|)[ \t]*make\b|\bmake\s+--?[a-z]|\bmake\s+[a-z_][a-z0-9_]*="
                rf"|\bmake\s+(?:{MAKE_TARGETS_ALWAYS})\b"
                rf"|\bmake(?:\s+(?:{MAKE_TARGETS_AT_CLAUSE_END}))+(?=[ \t]*(?:\n|$|[.;)|&]))")
EVAL_COMMAND = r"\beval\s+[\"'`$]|\beval\("
PATTERNS = [
    ("url", URL),
    ("bare_domain", r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|dev|ai|sh|co|app|xyz|me|info|biz|ly|gg|tv|fm|site|cloud)\b(?:/\S*)?"),
    ("markdown_link", r"\]\([^)]*\)"),
    ("email_address", r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    ("code", r"```|`[^`\n]+`"),
    ("shell_command", r"\b(?:curl|wget|sudo|bash|zsh|exec|chmod|chown|ssh|scp|rsync|nc|osascript|docker|kubectl)\b"
                      r"|\brm\s+-|\|\s*(?:ba|z)?sh\b|\bsh\s+-c\b|\bgit\s+(?:push|reset|clean|checkout\s+--)"
                      r"|\bpython3?\s+-c\b|\bnode\s+-e\b|" + MAKE_COMMAND + "|" + EVAL_COMMAND),
    ("run_or_execute", r"\b(?:execute|run (?:this|the following|these|a|the) (?:command|script|snippet)s?|run the setup)\b"),
    ("fetch_or_visit", r"\b(?:fetch|visit|go to|navigate to|browse to|retrieve|look up online|check online)\b"),
    ("install", r"\b(?:install|download|pip3?|npm|npx|brew|apt(?:-get)?|gem|cargo add|uvx?)\b"),
    ("permissions", r"\b(?:permission|allowed-tools|allowedtools|settings\.json|--dangerously|bypass|sandbox|auto-?approve|yolo)\w*"),
    ("skip_confirmation", r"\b(?:without (?:asking|confirmation|confirming|approval|review)|skip(?:ping)? (?:the )?(?:confirmation|review|approval|prompt)s?|don'?t ask|never ask|no need to ask)\b"),
    ("hide_from_user", r"\b(?:hide|conceal|quietly|silently|secretly|don'?t (?:tell|mention|show)|never (?:tell|mention|show)|without telling)\b"),
    ("contact", r"\b(?:e-?mail|send (?:it |this |them )?to|post (?:it |this )?to|notify|message|dm|tweet|share (?:it )?with|webhook|slack|telegram|discord|whatsapp|sms|contact)\b"),
    ("credentials", r"\b(?:api[_ -]?key|token|password|secret|credential|\.env|ssh key)s?\b"),
    ("encoded_blob", r"[A-Za-z0-9+/]{40,}={0,2}"),
    ("mixed_script", r"\b\w*(?:[a-z][Ͱ-ϿЀ-ӿ]|[Ͱ-ϿЀ-ӿ][a-z])\w*\b"),
]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
ALLOWED_FRONTMATTER_KEYS = ("name", "description")
PROVENANCE_ONE_LINE = re.compile(r"<!--\s*cast2skill:[^\n]{0,300}?-->")
TRAILING_SOURCE = re.compile(r"^##\s+Source[ \t]*\n((?:[^\n#][^\n]*\n?){0,2})\s*\Z", re.MULTILINE)


def without_urls(text):
    return re.sub(URL, "", text, flags=re.IGNORECASE)


def split_frontmatter(text):
    """(flags for disallowed keys, body text to scan including the description)."""
    found = FRONTMATTER.match(text)
    if not found:
        return [], text
    flags, kept = [], []
    for line in found.group(1).splitlines():
        key = line.split(":", 1)[0].strip()
        if not key:
            continue
        if key in ALLOWED_FRONTMATTER_KEYS:
            kept.append(line)
        else:
            flags.append({"rule": "frontmatter_key", "match": line.strip()[:80]})
    return flags, "\n".join(kept) + "\n" + text[found.end():]


def scannable_text(text):
    """NFKC text with only the exempt URLs removed."""
    normalized = unicodedata.normalize("NFKC", text or "").replace("\r\n", "\n")
    normalized = PROVENANCE_ONE_LINE.sub(lambda m: without_urls(m.group(0)), normalized)
    return TRAILING_SOURCE.sub(lambda m: without_urls(m.group(0)), normalized)


def check_lesson(text):
    flags, body = split_frontmatter(scannable_text(text))
    for name, pattern in PATTERNS:
        for found in re.finditer(pattern, body, flags=re.IGNORECASE):
            flags.append({"rule": name, "match": found.group(0)[:80]})
    return {"ok": not flags, "flags": flags,
            "verdict": "no flags; the safety rules still apply" if not flags else
            "note only: show the user the flagged parts as a quote, or remove that idea (not a reworded copy of it) and check again"}
