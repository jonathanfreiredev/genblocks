"""What must not travel from a private brief into a public block.

A brief is written for one person and one run; a published block is read by
everybody. The task keeps the brief because it is the record of what was asked.
The block keeps a short, redacted version because a visitor needs to know what
it is, not who asked for it or where they live.

The patterns are deliberately conservative: an email, a phone number, a street
address, a social-security-shaped number, a long payment-card-shaped number and
credentials embedded in a URL. They do not pretend to find every name; the
content policy tells people not to submit personal data, and this is the net
that catches the structured cases before publication.
"""

import re

REDACTED = "[redacted]"

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", re.IGNORECASE)
PHONE = re.compile(
    r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)",
    re.IGNORECASE,
)
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
STREET = re.compile(
    r"\b\d{1,6}\s+[A-Z][\w'-]*(?:\s+[A-Z][\w'-]*){0,3}\s+"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b",
    re.IGNORECASE,
)
URL_CREDENTIALS = re.compile(r"(https?://)[^/\s:@]+:[^/\s@]+@", re.IGNORECASE)


def redact_pii(value: str) -> str:
    """Return ``value`` with structured personal data replaced.

    Order matters: the email and URL rules run before the phone/card rules so a
    redacted address cannot be re-read as a number, and the card rule runs before
    the shorter SSN rule so a card-shaped number is not half-redacted.
    """
    if not value:
        return value

    redacted = URL_CREDENTIALS.sub(rf"\1{REDACTED}@", value)
    redacted = EMAIL.sub(REDACTED, redacted)
    redacted = CARD.sub(REDACTED, redacted)
    redacted = SSN.sub(REDACTED, redacted)
    redacted = STREET.sub(REDACTED, redacted)
    redacted = PHONE.sub(REDACTED, redacted)

    return " ".join(redacted.split())
