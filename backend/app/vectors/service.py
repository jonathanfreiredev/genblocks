"""What the registry remembers, and what it can be asked.

Two questions and no more: *is this block already here?* and *have we got this
picture?* Both are answered by nearest neighbours in the space the embedder
built, and both are answered with ids so the caller reads the rows themselves —
retrieval decides what to look at, Postgres decides what is true.

Vectors are an improvement, never a dependency: if the embedder or the store is
unavailable, remembering is a warning in the log and searching finds nothing. A
task does not fail because retrieval is having a bad day, and the chat still
works.
"""

import asyncio
import uuid
from dataclasses import dataclass

import chromadb
import structlog

from app.vectors import embed
from app.vectors.client import COMPONENTS, IMAGES, collection

logger = structlog.get_logger("app.vectors.service")


@dataclass(frozen=True, slots=True)
class Match:
    """One remembered artifact, and how far it is from what was asked."""

    id: uuid.UUID
    distance: float


async def remember_component(
    *,
    component_id: uuid.UUID,
    text: str,
    screenshot: bytes | None,
    slug: str,
    category: str,
) -> bool:
    """Remember one published block, by its words and its render.

    Returns whether it was remembered, so a caller can say so rather than guess.
    """
    vector = await _vector(text=text, image=screenshot)

    return await _store(
        COMPONENTS,
        component_id=component_id,
        vector=vector,
        text=text,
        metadata={"slug": slug, "category": category, "kind": "component"},
    )


async def remember_image(
    *,
    image_id: uuid.UUID,
    prompt: str,
    picture: bytes | None,
    category: str,
) -> bool:
    """Remember one picture in the library, by its prompt and the picture."""
    vector = await _vector(text=prompt, image=picture)

    return await _store(
        IMAGES,
        component_id=image_id,
        vector=vector,
        text=prompt,
        metadata={"category": category, "kind": "image"},
    )


async def find_components(text: str, *, limit: int = 5) -> list[Match]:
    """The published blocks nearest to a brief, nearest first."""
    return await _find(COMPONENTS, text=text, limit=limit)


async def find_images(text: str, *, limit: int = 3, category: str | None = None) -> list[Match]:
    """The library pictures nearest to a description, nearest first.

    ``category`` narrows to one type of image before the vector is compared: a
    photograph is not an illustration, however close the words are.
    """
    where = {"category": category} if category else None

    return await _find(IMAGES, text=text, limit=limit, where=where)


async def forget(collection_name: str, *, ids: list[uuid.UUID]) -> None:
    """Drop artifacts from the index, for a seed that is being rewritten."""
    if not ids:
        return

    try:
        await asyncio.to_thread(
            collection(collection_name).delete, ids=[str(one) for one in ids]
        )
    except Exception as broke:  # noqa: BLE001 - an index that lags is not an outage
        logger.warning("vectors forgot nothing", collection=collection_name, error=str(broke))


async def _vector(*, text: str, image: bytes | None) -> list[float] | None:
    try:
        if image is None:
            return await embed.embed_text(text)

        return await embed.embed_artifact(text=text, image=image)
    except embed.EmbeddingUnavailable as unavailable:
        logger.warning("vectors skipped", reason=str(unavailable))

        return None


async def _store(
    name: str,
    *,
    component_id: uuid.UUID,
    vector: list[float] | None,
    text: str,
    metadata: dict[str, str],
) -> bool:
    if vector is None:
        return False

    try:
        await asyncio.to_thread(
            collection(name).upsert,
            ids=[str(component_id)],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata],
        )
    except Exception as broke:  # noqa: BLE001 - the row is the truth, the vector is an index
        logger.warning("vectors not stored", collection=name, error=str(broke))

        return False

    return True


async def _find(
    name: str, *, text: str, limit: int, where: dict[str, str] | None = None
) -> list[Match]:
    try:
        vector = await embed.embed_text(text)
    except embed.EmbeddingUnavailable as unavailable:
        logger.warning("vectors not searched", reason=str(unavailable))

        return []

    try:
        answer = await asyncio.to_thread(
            collection(name).query,
            query_embeddings=[vector],
            n_results=limit,
            where=where,
        )
    except (chromadb.errors.ChromaError, ValueError) as broke:
        logger.warning("vectors not searched", collection=name, error=str(broke))

        return []

    ids = (answer.get("ids") or [[]])[0]
    distances = (answer.get("distances") or [[]])[0]

    return [
        Match(id=uuid.UUID(one), distance=float(distance))
        for one, distance in zip(ids, distances, strict=False)
    ]
