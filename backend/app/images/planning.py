"""The preflight every standalone image passes before it can be queued."""

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.categories import service as categories_service
from app.categories.models import CategoryKind
from app.image_policy import prompt as prompt_policy
from app.images.sizes import size_complaint
from app.moderation import service as moderation


@dataclass(frozen=True)
class ImagePlan:
    """What the chat, the API and the MCP answer with, before any task exists."""

    status: str
    prompt: str
    width: int
    height: int
    category: str
    category_id: uuid.UUID | None
    reason: str
    suggested_prompt: str | None

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    @property
    def needs_confirmation(self) -> bool:
        return self.status == "needs_image_confirmation"

    def as_body(self) -> dict:
        return {
            "status": self.status,
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            "category": self.category,
            "reason": self.reason,
            "suggested_prompt": self.suggested_prompt,
        }


class ImagePromptRejected(Exception):
    """The prompt is not buildable as written."""

    def __init__(self, plan: ImagePlan) -> None:
        self.plan = plan
        self.reason = plan.reason
        super().__init__(f"The image prompt was refused — {plan.reason}")


class ImageSuggestionRequired(Exception):
    """The prompt asks for incidental people, and a no-person rewrite is ready."""

    def __init__(self, plan: ImagePlan) -> None:
        self.plan = plan
        self.reason = plan.reason
        self.suggested_prompt = plan.suggested_prompt
        super().__init__(
            "This prompt asks for a picture with people. Generated images may not "
            f"contain people — {plan.reason} Try this instead: {plan.suggested_prompt}"
        )


async def plan_image(
    session: AsyncSession,
    *,
    prompt: str,
    width: int,
    height: int,
    category: str,
) -> ImagePlan:
    """Validate size, taxonomy and policy without generating anything."""
    if complaint := size_complaint(width, height):
        return _rejected(
            prompt=prompt,
            width=width,
            height=height,
            category=category,
            category_id=None,
            reason=complaint,
        )

    found = await categories_service.get_category_by_slug(session, slug=category)
    if found is None or found.kind != CategoryKind.IMAGE or found.level != 2:
        return _rejected(
            prompt=prompt,
            width=width,
            height=height,
            category=category,
            category_id=None,
            reason=f"There is no image category named {category!r}.",
        )

    decision = await prompt_policy.evaluate(prompt)

    # A model that says "ready" while also saying there is a person is not a
    # decision this service will trust. The bytes gate would catch the picture,
    # but the person should not have reached generation at all.
    if decision.has_people and decision.status == "ready":
        if decision.suggested_prompt:
            decision = prompt_policy.PromptDecision(
                status="needs_image_confirmation",
                has_people=True,
                people_role=decision.people_role,
                reason=decision.reason,
                suggested_prompt=decision.suggested_prompt,
            )
        else:
            decision = prompt_policy.PromptDecision(
                status="rejected",
                has_people=True,
                people_role=decision.people_role,
                reason=decision.reason,
                suggested_prompt=None,
            )

    if decision.status == "rejected":
        return _rejected(
            prompt=prompt,
            width=width,
            height=height,
            category=category,
            category_id=found.id,
            reason=decision.reason,
        )

    if decision.status == "needs_image_confirmation":
        if decision.suggested_prompt is None:
            return _rejected(
                prompt=prompt,
                width=width,
                height=height,
                category=category,
                category_id=found.id,
                reason="The prompt asks for people, and there is no useful version without them.",
            )

        return ImagePlan(
            status="needs_image_confirmation",
            prompt=prompt,
            width=width,
            height=height,
            category=category,
            category_id=found.id,
            reason=decision.reason,
            suggested_prompt=decision.suggested_prompt,
        )

    # The structured policy may miss a different prohibited category. The
    # established image-prompt gate is the final word on the prompt that will
    # actually be sent to BFL.
    why = await moderation.image_prompt_refusal(prompt)
    if why is not None:
        return _rejected(
            prompt=prompt,
            width=width,
            height=height,
            category=category,
            category_id=found.id,
            reason=why,
        )

    return ImagePlan(
        status="ready",
        prompt=prompt,
        width=width,
        height=height,
        category=category,
        category_id=found.id,
        reason=decision.reason,
        suggested_prompt=None,
    )


def _rejected(
    *,
    prompt: str,
    width: int,
    height: int,
    category: str,
    category_id: uuid.UUID | None,
    reason: str,
) -> ImagePlan:
    return ImagePlan(
        status="rejected",
        prompt=prompt,
        width=width,
        height=height,
        category=category,
        category_id=category_id,
        reason=reason,
        suggested_prompt=None,
    )
