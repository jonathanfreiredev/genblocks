"""The application's authorization vocabulary and the check that enforces it.

Authentication answers *who is this*; this module answers *what may they do*.
Permissions are scoped to an organization, because every domain row hangs off
one: what grants a caller is their role in the owning organization.

``ROLE_PERMISSIONS`` is the only place an authorization decision is written down.
Deliberately free of HTTP and of any domain module, so the API, the MCP tools and
tests all resolve permissions the same way.
"""

from collections.abc import Mapping
from enum import StrEnum


class MembershipRole(StrEnum):
    """The roles a user can hold inside an organization.

    Kept deliberately small: permissions derive from the role, so adding one is a
    decision about what it may do, not just a new string.
    """

    OWNER = "owner"
    MEMBER = "member"


class Permission(StrEnum):
    """What a caller may do, named ``<resource>:<action>``."""

    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"


class PermissionDenied(Exception):
    """Raised when a role does not grant the permission being required.

    A domain error, not an HTTP one: the MCP tools call the same code and report
    failures their own way. ``app/main.py`` translates it into a 403.
    """


# The policy table: what each role grants. ``MembershipRole`` hashes as its
# value, so the map can be keyed by the enum while lookups use the plain string
# that comes back from the database.
ROLE_PERMISSIONS: Mapping[str, frozenset[Permission]] = {
    MembershipRole.OWNER: frozenset({Permission.ORGANIZATION_READ, Permission.ORGANIZATION_UPDATE}),
    MembershipRole.MEMBER: frozenset({Permission.ORGANIZATION_READ}),
}


def require(permission: Permission, *, role: str) -> None:
    """Raise ``PermissionDenied`` unless ``role`` grants ``permission``.

    Deny by default: a role the table does not list grants nothing, so a role
    that reaches the database without a policy here is powerless instead of
    accidentally powerful.
    """
    if permission not in ROLE_PERMISSIONS.get(role, frozenset()):
        raise PermissionDenied(f"Missing permission: {permission.value}")
