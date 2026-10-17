"""What one turn of the conversation sends.

The conversation is named by the dialog, not by the API: a second tab is a second
conversation, and the endpoint only has to keep the turns of one apart from the
turns of another. The same bounds as the backend are enforced on both sides, and
these are the ones a message has — the brief it turns into has its own, in
``app/tasks/schemas.py``.
"""

from typing import Annotated

from pydantic import BaseModel, StringConstraints

MESSAGE_MAX_LENGTH = 4000
THREAD_MIN_LENGTH = 8
THREAD_MAX_LENGTH = 100

Message = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=MESSAGE_MAX_LENGTH,
    ),
]

ThreadId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=THREAD_MIN_LENGTH,
        max_length=THREAD_MAX_LENGTH,
    ),
]


class ChatRequest(BaseModel):
    """One turn: what the person said, and which conversation it belongs to."""

    message: Message
    thread_id: ThreadId
