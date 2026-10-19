"""What one turn of the graph becomes on the wire.

The reader is the seam between langgraph and the dialog, and these are the shapes
the graph actually emits — taken from a real run, not from the documentation — so
a change in how it streams is a test that fails rather than a dialog that goes
quiet. Nothing here needs a model or a database.
"""

import uuid
from datetime import UTC, datetime

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage

from app.agent.schemas import Suggestion, Suggestions
from app.agent.stream import Event, TurnReader, encode
from app.tasks.models import Task

BRIEF = "A pricing page for a developer tool: three tiers and an annual toggle."


def task() -> Task:
    """A task, as the queue has just written it."""
    return Task(
        id=uuid.uuid4(),
        kind="generate_component",
        status="pending",
        brief=BRIEF,
        created_at=datetime.now(UTC),
    )


def test_an_event_is_a_name_and_one_line_of_json():
    frame = encode(Event("token", {"text": "Queued"}))

    assert frame == 'event: token\ndata: {"text": "Queued"}\n\n'


def test_the_words_arrive_as_tokens():
    events = TurnReader(queued=[], suggested=Suggestions()).read(AIMessageChunk(content="Queued"))

    assert events == [Event("token", {"text": "Queued"})]


def test_a_wordless_chunk_says_nothing():
    # The graph closes a streamed call with an empty chunk, and a model thinking
    # about a tool has nothing to say. Neither is a token.
    assert TurnReader(queued=[], suggested=Suggestions()).read(AIMessageChunk(content="")) == []


def test_a_call_is_announced_once_however_many_pieces_it_arrives_in():
    reader = TurnReader(queued=[], suggested=Suggestions())

    first = reader.read(
        AIMessageChunk(
            content="",
            tool_call_chunks=[
                {"name": "search_components", "args": "", "id": "call_1", "index": 0}
            ],
        )
    )
    middle = reader.read(
        AIMessageChunk(
            content="",
            tool_call_chunks=[{"name": None, "args": '{"query":', "id": None, "index": 0}],
        )
    )
    whole = reader.read(
        AIMessageChunk(
            content="",
            tool_calls=[
                {
                    "name": "search_components",
                    "args": {"query": "pricing"},
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        )
    )

    assert first == [Event("tool", {"name": "search_components", "state": "started"})]
    assert middle == []
    assert whole == []


def test_a_call_that_arrives_whole_is_announced_too():
    events = TurnReader(queued=[], suggested=Suggestions()).read(
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "create_component",
                    "args": {"brief": BRIEF},
                    "id": "call_2",
                    "type": "tool_call",
                }
            ],
        )
    )

    assert events == [Event("tool", {"name": "create_component", "state": "started"})]


def test_a_tool_that_answered_is_finished():
    events = TurnReader(queued=[], suggested=Suggestions()).read(
        ToolMessage(content="{}", name="search_components", tool_call_id="call_1")
    )

    assert events == [Event("tool", {"name": "search_components", "state": "finished"})]


def test_the_task_a_tool_queued_reaches_the_dialog_with_the_answer():
    queued = [task()]
    reader = TurnReader(queued=queued, suggested=Suggestions())

    after = reader.read(ToolMessage(content="{}", name="create_component", tool_call_id="call_2"))
    end = reader.close()

    assert [event.name for event in after] == ["tool", "task"]
    shown = after[1].data
    assert shown["id"] == str(queued[0].id)
    assert shown["kind"] == "generate_component"
    assert shown["status"] == "pending"
    assert shown["brief"] == BRIEF
    assert shown["component_id"] is None
    assert shown["steps"] == []
    # The end of the turn repeats nothing: the task is already on the wire.
    assert [event.name for event in end] == ["done"]


def test_a_turn_ends_whether_or_not_it_queued_anything():
    assert TurnReader(queued=[], suggested=Suggestions()).close() == [Event("done", {})]


def test_a_message_the_reader_does_not_know_is_left_alone():
    reader = TurnReader(queued=[], suggested=Suggestions())

    assert reader.read(HumanMessage(content="build a hero")) == []


def test_what_a_tool_found_reaches_the_dialog_once():
    suggested = Suggestions()
    reader = TurnReader(queued=[], suggested=suggested)
    block = Suggestion(
        kind="component",
        id=uuid.uuid4(),
        title="Tiered pricing",
        detail="Three plans in a ruled table",
        path="genblocks/screenshots/abc-1",
    )
    suggested.add(block)

    first = reader.read(ToolMessage(content="{}", name="search_components", tool_call_id="c1"))
    second = reader.read(ToolMessage(content="{}", name="search_components", tool_call_id="c2"))

    assert [event.name for event in first] == ["tool", "suggestions"]
    assert first[1].data == {"items": [block.as_body()]}
    # A second search that finds the same block does not draw it twice.
    assert [event.name for event in second] == ["tool"]
