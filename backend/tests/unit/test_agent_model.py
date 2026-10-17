"""The model the conversation runs on, and the key it needs to exist.

The key is optional everywhere else in this service so that the API boots without
it. Here it stops a turn, and it has to say so in a way the dialog can show.
"""

import pytest
from fastapi import HTTPException
from langchain_openai import ChatOpenAI

from app.agent.model import get_chat_model
from app.settings import settings


def test_a_deployment_with_no_key_is_told_what_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(HTTPException) as refused:
        get_chat_model()

    assert refused.value.status_code == 503
    assert "OPENAI_API_KEY" in refused.value.detail


def test_the_conversation_runs_on_the_configured_model(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "llm_model", "gpt-6-luna")

    model = get_chat_model()

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-6-luna"
    # Token by token, or there is no stream for the dialog to read.
    assert model.streaming is True
