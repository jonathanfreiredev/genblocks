import pytest

from app.authz.permissions import MembershipRole, Permission, PermissionDenied, require


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (MembershipRole.OWNER, Permission.ORGANIZATION_READ),
        (MembershipRole.OWNER, Permission.ORGANIZATION_UPDATE),
        (MembershipRole.MEMBER, Permission.ORGANIZATION_READ),
    ],
)
def test_a_role_grants_its_permissions(role: str, permission: Permission):
    require(permission, role=role)  # does not raise


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (MembershipRole.MEMBER, Permission.ORGANIZATION_UPDATE),
        # Deny by default: a role the policy table does not list grants nothing.
        ("role-from-an-older-migration", Permission.ORGANIZATION_READ),
    ],
)
def test_a_role_without_the_permission_is_denied(role: str, permission: Permission):
    with pytest.raises(PermissionDenied):
        require(permission, role=role)
