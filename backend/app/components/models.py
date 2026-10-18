import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel

# Every generated artifact ships under the same permissive license.
DEFAULT_LICENSE = "MIT"


class Component(BaseModel):
    """A published UI block: the code a visitor copies, plus the judge's record."""

    __tablename__ = "components"

    slug: Mapped[str] = mapped_column(unique=True, index=True)
    title: Mapped[str]
    description: Mapped[str]
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    code: Mapped[str]
    # The whole project: path → file, as the harness left it. ``code`` is the entry
    # file, kept beside it because it is what the read API and the MCP door have
    # always answered with — a block that grew files must not break a client that
    # only ever asked for one.
    files: Mapped[dict | None] = mapped_column(JSONB)
    # What it imports from packages, with the version it was built against: the
    # install line a visitor needs, read from the project by the sandbox rather
    # than declared by the model that wrote it.
    dependencies: Mapped[dict | None] = mapped_column(JSONB)
    # What a visitor would type to get this block: the brief that produced it,
    # cleaned up.
    delivery_prompt: Mapped[str]
    # The spec the harness was handed, kept as JSON so it can evolve without a
    # migration.
    spec: Mapped[dict | None] = mapped_column(JSONB)
    # The attempt that was published. Created after ``generations`` exists,
    # because the two tables point at each other (``use_alter``). With one artifact
    # per task this is simply "the run this block came from".
    winning_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generations.id", ondelete="SET NULL", use_alter=True), index=True
    )
    # Nullable: seeded blocks predate any user, and a block outlives its author.
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    license: Mapped[str] = mapped_column(default=DEFAULT_LICENSE)


class ComponentAsset(BaseModel):
    """Links a block to one of the stock images it uses, in a named slot.

    A slot is unique per component, so reusing the same image in two places is
    two rows, and a re-run cannot leave two images claiming slot "hero".
    """

    __tablename__ = "component_assets"

    __table_args__ = (
        UniqueConstraint("component_id", "slot", name="uq_component_assets_component_slot"),
    )

    component_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("components.id", ondelete="CASCADE"), index=True
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), index=True
    )
    slot: Mapped[str]
