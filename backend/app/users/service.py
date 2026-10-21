import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.claims import TokenClaims
from app.db.models import utcnow
from app.users.models import User


async def get_user(session: AsyncSession, *, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def list_users(
    session: AsyncSession,
    *,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[User], int]:
    """A page of profiles for the operator's ban screen."""
    statement = select(User)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))

    total = await session.scalar(select(func.count()).select_from(statement.subquery()))
    found = await session.scalars(
        statement.order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    return found.all(), total or 0


async def set_ban(
    session: AsyncSession,
    *,
    user: User,
    operator: User,
    banned: bool,
    reason: str | None = None,
) -> User:
    """Ban or unban one profile. Authorization is the caller's job."""
    if banned:
        user.banned_at = utcnow()
        user.banned_by = operator.id
        user.ban_reason = reason.strip() if reason and reason.strip() else None
    else:
        user.banned_at = None
        user.banned_by = None
        user.ban_reason = None

    await session.commit()
    await session.refresh(user)
    return user


async def display_names(
    session: AsyncSession, *, ids: Sequence[uuid.UUID | None]
) -> dict[uuid.UUID, str]:
    """The public name of each author, by user id.

    Only the display name: an email is the account's, not the gallery's, and a
    profile without a name stays anonymous rather than leaking the address a
    visitor would otherwise never see.
    """
    wanted = [one for one in ids if one is not None]
    if not wanted:
        return {}

    found = await session.execute(
        select(User.id, User.full_name).where(User.id.in_(wanted), User.full_name.is_not(None))
    )

    return {user_id: name for user_id, name in found.all() if name}


async def get_or_create_user(session: AsyncSession, claims: TokenClaims) -> User:
    """Return the profile for the authenticated subject, creating it on first use.

    Supabase owns signup, so the local profile is provisioned just-in-time: the
    first authenticated request creates it and the mirrored email is kept in
    sync on later requests.
    """
    user = await _find_by_subject(session, claims.subject)

    if user is None:
        user = await _create_user(session, claims)

    if claims.email and user.email != claims.email:
        user.email = claims.email
        await session.commit()
        await session.refresh(user)

    return user


async def _find_by_subject(session: AsyncSession, subject: uuid.UUID) -> User | None:
    return await session.scalar(select(User).where(User.supabase_user_id == subject))


async def _create_user(session: AsyncSession, claims: TokenClaims) -> User:
    """Insert the profile, tolerating a concurrent insert for the same subject.

    Two first requests from the same user can race: both miss the lookup and try
    to insert. The unique constraint on ``supabase_user_id`` turns the loser's
    insert into a no-op (``ON CONFLICT DO NOTHING``) instead of a 500, and the
    row the winner created is read back and returned.
    """
    statement = (
        insert(User)
        .values(
            supabase_user_id=claims.subject,
            email=claims.email,
            full_name=claims.metadata.get("full_name"),
        )
        .on_conflict_do_nothing(index_elements=["supabase_user_id"])
    )
    await session.execute(statement)
    await session.commit()

    created = await _find_by_subject(session, claims.subject)
    if created is None:  # pragma: no cover - the row must exist after the insert
        raise RuntimeError("User provisioning failed: no profile after insert")

    return created
