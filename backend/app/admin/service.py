"""The global operator role.

Organization roles answer "what may this person do inside this tenant". The
report queue is not a tenant concern: one report can point at any public block,
and an owner of one organization must not be able to remove another's work.
Operators are therefore configured by email, not by a membership row, and the
check lives in the service so a router cannot forget it.
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
