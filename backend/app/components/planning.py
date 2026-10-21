"""The single preflight a component brief goes through before it is queued.

It combines the text safety gate with the image-direction policy. Every entrance
(the chat agent, the MCP server and the HTTP task route) reaches this module
through ``app.tasks.service.enqueue_task``; a caller cannot skip it by writing a
brief straight into the queue.
"""

from dataclasses import dataclass

from app.image_policy import service as image_policy
from app.moderation import service as moderation


@dataclass(frozen=True)
class PlanDecision:
    """What the caller should do with a brief before it becomes a task."""

    status: str
    brief: str
    reason: str
    proposed_brief: str | None
    image_policy: image_policy.ImagePolicyDecision | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    @property
    def needs_confirmation(self) -> bool:
        return self.status == "needs_image_confirmation"

    def as_body(self) -> dict:
        return {
            "status": self.status,
            "brief": self.brief,
            "reason": self.reason,
            "proposed_brief": self.proposed_brief,
        }


class ImageConfirmationRequired(Exception):
    """The brief asks for people, and a no-person rewrite is available."""

    def __init__(self, *, reason: str, proposed_brief: str) -> None:
        self.reason = reason
        self.proposed_brief = proposed_brief
        super().__init__(
            "This brief asks for a picture with people. Generated images may not "
            f"contain people — {reason} Try this instead: {proposed_brief}"
        )


async def plan(brief: str) -> PlanDecision:
    """Classify a brief without queueing anything."""
    why = await moderation.refusal(brief)
    if why is not None:
        return PlanDecision(
            status="rejected",
            brief=brief,
            reason=why,
            proposed_brief=None,
        )

    direction = await image_policy.evaluate(brief)
    if direction.status == "rejected":
        return PlanDecision(
            status="rejected",
            brief=brief,
            reason=direction.reason,
            proposed_brief=None,
            image_policy=direction,
        )

    if direction.status == "needs_image_confirmation":
        if direction.proposed_brief is None:
            return PlanDecision(
                status="rejected",
                brief=brief,
                reason=("The brief asks for people, and there is no useful version without them."),
                proposed_brief=None,
                image_policy=direction,
            )

        return PlanDecision(
            status="needs_image_confirmation",
            brief=brief,
            reason=direction.reason,
            proposed_brief=direction.proposed_brief,
            image_policy=direction,
        )

    return PlanDecision(
        status="ready",
        brief=brief,
        reason=direction.reason,
        proposed_brief=None,
        image_policy=direction,
    )
