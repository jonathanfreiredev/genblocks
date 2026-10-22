"""The global operator role.

The report queue is not scoped to an organization: one report can point at any
public block or image. Operators are configured by email, not by a membership
row, and the check lives in the service so a router cannot forget it. The
organization roles in ``app/authz`` belong to the template endpoints only.
"""

from app.authz.permissions import PermissionDenied
from app.settings import settings
from app.users.models import User


def is_admin(user: User) -> bool:
    """Whether this profile is one of the configured operators."""
    email = (user.email or "").strip().lower()
    return bool(email) and email in settings.admin_email_list


def require_admin(user: User) -> None:
    if not is_admin(user):
        raise PermissionDenied("Only an operator may review reports.")
