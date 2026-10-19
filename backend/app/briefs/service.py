"""The briefs the registry has already answered.

A cache, not a judgement: the key is the brief's own words, normalized, and
nothing is inferred from them. "A hero with a headline" and "a hero, one headline"
are two briefs here, because only the person who wrote them knows whether they
mean the same thing — and the guard already asks them.

What it saves is a run: the model, the sandbox, the images and the judge. What it
must never do is answer with something that is no longer there, so a lookup joins
the block and a deleted block is a miss.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.briefs.models import BriefCache
from app.components.models import Component


def key_for(brief: str) -> str:
    """The brief as a cache key: lowercased, whitespace collapsed, nothing else.

    Case and spacing are typing; word choice is meaning, and meaning is not this
    module's to decide.
    """
    return " ".join(brief.lower().split())


async def find(session: AsyncSession, *, brief: str) -> Component | None:
    """The block that answered this exact brief, if it is still in the registry."""
    return await session.scalar(
        select(Component)
        .join(BriefCache, BriefCache.component_id == Component.id)
        .where(
            BriefCache.key == key_for(brief),
            BriefCache.deleted_at.is_(None),
            Component.deleted_at.is_(None),
        )
    )


async def remember(session: AsyncSession, *, brief: str, component_id: uuid.UUID) -> None:
    """Point this brief at the block that answered it.

    Written in the transaction that publishes the block, and an upsert because the
    same brief can be built twice — two tasks queued before either published, or a
    forced rebuild — and the second answer is the one to keep.
    """
    statement = (
        insert(BriefCache)
        .values(id=uuid.uuid4(), key=key_for(brief), component_id=component_id)
        .on_conflict_do_update(
            index_elements=[BriefCache.key],
            set_={"component_id": component_id, "deleted_at": None},
        )
    )

    await session.execute(statement)
