"""The URLs a provider is allowed to send us back to.

A provider response is data, not an instruction to fetch anything it names. BFL
answers with a polling URL and, later, a signed sample URL; taking either as-is
would make a compromised or confused provider response into an SSRF primitive
inside the worker's network. The same rule applies to every provider that later
adds an asynchronous callback.

The check is deliberately an exact host allowlist on top of HTTPS and the
absence of credentials. Resolving a hostname and checking the address would not
be enough on its own: the resolution and the connection are two different
moments, which is the DNS-rebinding gap. An exact host we chose does not have
that gap.
"""

from ipaddress import ip_address
from urllib.parse import urlsplit


class UnsafeProviderUrl(Exception):
    """A provider named a URL this service will not fetch."""


def checked_provider_url(
    value: object,
    *,
    hosts: tuple[str, ...],
    what: str,
) -> str:
    """Return ``value`` when it is a safe HTTPS URL on one of ``hosts``.

    ``what`` names the URL in the refusal so a task's error says which provider
    answer was rejected, not merely that something was.
    """
    if not isinstance(value, str) or not value.strip():
        raise UnsafeProviderUrl(f"The provider did not answer with a {what} URL.")

    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https":
        raise UnsafeProviderUrl(f"The {what} URL is not HTTPS: {value}.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeProviderUrl(f"The {what} URL carries credentials.")
    if parsed.port not in (None, 443):
        raise UnsafeProviderUrl(f"The {what} URL uses an unexpected port.")

    host = (parsed.hostname or "").rstrip(".").lower()
    if host not in hosts:
        raise UnsafeProviderUrl(f"The {what} URL names {host or 'no host'}, which is not allowed.")

    # An allowlist entry could itself be an address. Private, loopback, link-local
    # and reserved addresses are never a provider's public asset host.
    try:
        address = ip_address(host)
    except ValueError:
        return value

    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
        raise UnsafeProviderUrl(f"The {what} URL points at a private address.")

    return value
