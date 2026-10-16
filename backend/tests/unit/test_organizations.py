import pytest

from app.organizations.service import _slugify


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Acme", "acme"),
        ("Acme Corp", "acme-corp"),
        # Accents are decomposed and the combining marks dropped.
        ("Café Ñandú", "cafe-nandu"),
        ("  spaced  out  ", "spaced-out"),
        ("weird!!!chars???", "weird-chars"),
        # A name with nothing usable left still has to produce a slug.
        ("---", "organization"),
        ("", "organization"),
    ],
)
def test_slugify(name: str, expected: str):
    assert _slugify(name) == expected
