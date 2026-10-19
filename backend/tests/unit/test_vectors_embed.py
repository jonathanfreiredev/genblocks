"""What the embedder hands back, and in what shape.

The shape is the whole test: the endpoint answers a *list* of vectors because it
can take a batch, and a single search that passed the list on as one embedding
failed at the store and looked exactly like a registry with nothing in it. That
bug is why these exist.
"""

import pytest

from app.vectors import embed

pytestmark = pytest.mark.anyio

VECTOR = [0.25, -0.5, 0.75]


async def test_a_sentence_comes_back_as_one_flat_vector(monkeypatch):
    async def fake(inputs):
        return [VECTOR for _ in inputs]

    monkeypatch.setattr(embed, "embed", fake)

    assert await embed.embed_text("a pricing table") == VECTOR


async def test_an_artifact_comes_back_as_one_flat_vector(monkeypatch):
    seen: list = []

    async def fake(inputs):
        seen.append(inputs)
        return [VECTOR]

    monkeypatch.setattr(embed, "embed", fake)

    assert await embed.embed_artifact(text="a hero", image=b"\x89PNG") == VECTOR
    # Both halves go in one input: the vector is of the pair, not of the words.
    assert [part["type"] for part in seen[0][0]] == ["text", "image_base64"]


async def test_a_batch_keeps_the_order_it_was_given(monkeypatch):
    async def fake(inputs):
        return [[float(index)] for index, _ in enumerate(inputs)]

    monkeypatch.setattr(embed, "embed", fake)

    vectors = await embed.embed([[{"type": "text", "text": one}] for one in ("a", "b", "c")])

    assert vectors == [[0.0], [1.0], [2.0]]
