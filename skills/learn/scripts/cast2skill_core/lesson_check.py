"""`check`: a mechanical backstop for SPEC section 10, rule 2.

A lesson that will be written as a skill or a CLAUDE.md rule steers future
sessions, and its words may come from an untrusted transcript. This scans the
instruction text for what such a lesson must never tell the agent to do: run
a command, fetch a URL, install something, change permissions, skip
confirmations, hide information from the user, or contact anyone.

It is deliberately strict and will flag some harmless text. The skill treats
any flag as "this can only be a note, shown as a quote", unless the flagged
part is removed. The `## Source` section and the `<!-- cast2skill: ... -->`
provenance comment are skipped, since they carry the source URL by design.
"""

import re

PATTERNS = [
    ("url", r"\b(?:https?|ftp)://\S+|\bwww\.\S+"),
    ("code_block", r"```"),
    ("shell_command", r"\b(?:curl|wget|sudo|bash|zsh|sh -c|eval|exec|chmod|chown|rm -rf|ssh|scp|nc)\b|\|\s*(?:ba|z)?sh\b"),
    ("install", r"\b(?:install|download|pip3?|npm|npx|brew|apt(?:-get)?|gem|cargo add|uvx?)\b"),
    ("permissions", r"\b(?:permission|allowed-tools|allowedtools|settings\.json|--dangerously|bypass|sandbox|auto-?approve|yolo)\w*"),
    ("skip_confirmation", r"\b(?:without (?:asking|confirmation|confirming|approval)|skip(?:ping)? (?:the )?(?:confirmation|review|approval|prompt)s?|don'?t ask|never ask|no need to ask)\b"),
    ("hide_from_user", r"\b(?:hide|conceal|silently|secretly|don'?t (?:tell|mention|show)|never (?:tell|mention|show)|without telling)\b"),
    ("contact", r"\b(?:e-?mail|send (?:it |this |them )?to|post (?:it |this )?to|webhook|slack|telegram|discord|whatsapp|sms|contact)\b"),
    ("credentials", r"\b(?:api[_ -]?key|token|password|secret|credential|\.env|ssh key)s?\b"),
]
PROVENANCE_COMMENT = re.compile(r"<!--\s*cast2skill:.*?-->", re.DOTALL)
SOURCE_SECTION = re.compile(r"^##\s+Source\b.*?(?=^##\s|\Z)", re.DOTALL | re.MULTILINE)
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def instruction_text(text):
    """The part of a lesson that instructs: minus provenance, Source section, frontmatter."""
    without_comment = PROVENANCE_COMMENT.sub("", text or "")
    without_source = SOURCE_SECTION.sub("", without_comment)
    frontmatter = FRONTMATTER.match(without_source)
    if frontmatter:
        # keep the description: it decides when the skill runs
        description = re.findall(r"^description:.*$", frontmatter.group(0), re.MULTILINE)
        without_source = "\n".join(description) + "\n" + without_source[frontmatter.end():]
    return without_source


def check_lesson(text):
    body = instruction_text(text)
    flags = []
    for name, pattern in PATTERNS:
        for found in re.finditer(pattern, body, flags=re.IGNORECASE):
            flags.append({"rule": name, "match": found.group(0)[:80]})
    return {"ok": not flags, "flags": flags,
            "verdict": "may be written as a skill or rule" if not flags else
            "note only: show the user the flagged parts as a quote, or remove them and check again"}
