"""The visual no-people gate, read as a strict answer rather than prose."""

import json

import httpx
import pytest

from app.moderation import people

pytestmark = pytest.mark.anyio


class Vision:
    """A vision model answered without a provider."""

    def __init__(self, *, has_human: bool, reason: str = "a hand is visible") -> None:
        self.has_human = has_human
        self.reason = reason
        self.asked: dict = {}

    async def post(self, url: str, *, headers: dict, json: dict) -> httpx.Response:
        self.asked = {"url": url, "headers": headers, "body": json}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {"has_human": self.has_human, "reason": self.reason}
                            )
                        }
                    }
                ]
            },
            request=httpx.Request("POST", url),
        )


# Keep the name distinct from the argument named ``json`` in ``post``.
json_module = json


async def test_a_human_is_a_refusal():
    answer = await people.people_refusal(
        b"jpeg-bytes", media_type="image/jpeg", client=Vision(has_human=True)
    )

    assert answer == "a hand is visible"


async def test_an_object_scene_passes():
    answer = await people.people_refusal(
        b"jpeg-bytes", media_type="image/jpeg", client=Vision(has_human=False)
    )

    assert answer is None


async def test_an_unreadable_answer_is_not_a_pass():
    class Broken:
        async def post(self, *args, **kwargs) -> httpx.Response:
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "not json"}}]},
                request=httpx.Request("POST", "https://example.test"),
            )

    with pytest.raises(people.PeopleCheckUnavailable):
        await people.people_refusal(b"jpeg-bytes", client=Broken())
