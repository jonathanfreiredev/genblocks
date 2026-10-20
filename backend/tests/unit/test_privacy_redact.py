from app.privacy.redact import REDACTED, redact_pii


def test_an_email_does_not_reach_a_published_block():
    assert redact_pii("Ask Jane at jane@example.com for the copy") == (
        f"Ask Jane at {REDACTED} for the copy"
    )


def test_a_phone_number_is_redacted():
    assert redact_pii("Call +1 (555) 123-4567 today") == f"Call {REDACTED} today"


def test_a_street_address_is_redacted():
    assert redact_pii("Ship it to 42 Market Street, please") == (f"Ship it to {REDACTED}, please")


def test_payment_and_government_numbers_are_redacted():
    text = "card 4111 1111 1111 1111 and ssn 123-45-6789"
    redacted = redact_pii(text)

    assert "4111" not in redacted
    assert "123-45-6789" not in redacted
    assert redacted.count(REDACTED) == 2


def test_url_credentials_are_redacted():
    assert redact_pii("see https://user:secret@example.com/x") == (
        f"see https://{REDACTED}@example.com/x"
    )


def test_ordinary_ui_copy_keeps_its_numbers():
    assert redact_pii("Three plans, from $19 to $99") == "Three plans, from $19 to $99"
