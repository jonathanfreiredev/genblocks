"""Turning a block, a picture or a brief into a vector.

One embedder for all three, and it is multimodal: ``voyage-multimodal-3`` puts
text and images in the same space, which is the whole reason a brief can be
compared with a screenshot. A text-only embedder would answer "does this title
sound like that one", and the question is "does this page already exist".

The call is the expensive part of retrieval, so it is one request per thing
embedded, and every failure is a typed refusal the caller decides what to do
with: vectors are an improvement, and nothing in the pipeline may fail because
the embedder is having a day.
"""

from collections.abc import Sequence
from typing import Any

import httpx

from app.settings import settings

ENDPOINT = "https://api.voyageai.com/v1/multimodalembeddings"

# What kind of content one part is: the words that describe the artifact, and the
# artifact itself. Both go into one input, so the vector is of the pair.
TEXT = "text"
IMAGE = "image_base64"


class EmbeddingUnavailable(Exception):
    """There is no embedder configured, or it did not answer."""


async def embed_text(text: str) -> list[float]:
    """The vector of a sentence — a brief, a title, a search."""
    return await embed([[{"type": TEXT, "text": text}]])


async def embed_artifact(*, text: str, image: bytes, media_type: str = "image/png") -> list[float]:
    """The vector of an artifact: what it is called, and what it looks like.

    Both halves matter and neither alone is enough: the picture carries the design
    and the words carry the intent, and two blocks that look alike can be for
    different jobs.
    """
    return (
        await embed(
            [
                [
                    {"type": TEXT, "text": text},
                    {"type": IMAGE, "image_base64": _data_url(image, media_type)},
                ]
            ]
        )
    )[0]


async def embed(inputs: Sequence[list[dict[str, Any]]]) -> list[list[float]]:
    """The vectors of several inputs in one request, in the order given."""
    if not settings.voyage_api_key:
        raise EmbeddingUnavailable("No embedder is configured: set VOYAGE_API_KEY on the API.")

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            answer = await client.post(
                ENDPOINT,
                headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
                json={
                    "model": settings.embedding_model,
                    "inputs": [{"content": one} for one in inputs],
                },
            )
        except httpx.HTTPError as broke:
            raise EmbeddingUnavailable(f"The embedder did not answer: {broke}") from broke

    if answer.status_code != 200:
        raise EmbeddingUnavailable(
            f"The embedder refused the request ({answer.status_code}): {answer.text[:200]}"
        )

    return [one["embedding"] for one in answer.json()["data"]]


def _data_url(image: bytes, media_type: str) -> str:
    """Image bytes as the embedder takes them: a data URL, since nothing is hosted."""
    import base64

    return f"data:{media_type};base64,{base64.b64encode(image).decode()}"
