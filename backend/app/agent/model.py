"""The model the conversation runs on.

Handed to the endpoint as a dependency rather than built inside the graph, so a
test can run the same graph on a scripted model, and so the key is required in
exactly one place.
"""

from fastapi import HTTPException, status
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.settings import settings


def get_chat_model() -> BaseChatModel:
    """The agent's model, or a 503 when the deployment has no key for it.

    It streams, and it has to: the graph only emits a token at a time when the
    model does, and an answer that arrives whole is not a conversation.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The agent has no model configured: set OPENAI_API_KEY on the API.",
        )

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        streaming=True,
    )
