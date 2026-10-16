import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.claims import TokenClaims
from app.users.models import User


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
