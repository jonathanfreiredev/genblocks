"""The checklist a task publishes, and which line of it costs money.

The runner writes these steps and marks them as it goes; the quota reads them to
tell a run that died before it cost anything from one that was paid for. They live
here rather than in the runner because the two modules that need them — the runner
that writes them and the limit that counts them — cannot import each other: the
runner imports the task service, and the service imports the limit.

The order is part of the contract. Index 1 is the expensive step in both lists: the
build in a component task, the provider call in an image task. Everything before it
is a model call of cents; everything after it has already been paid for.
"""

STEP_NAMES = (
    "Retrieving references",
    "Generating the block",
    "Judging the attempt",
    "Publishing the block",
)

IMAGE_STEP_NAMES = (
    "Checking the prompt",
    "Generating the image",
    "Judging the image",
    "Filing it in the library",
)

# The step whose start is the point of no return for the bill.
GENERATING_STEPS = (STEP_NAMES[1], IMAGE_STEP_NAMES[1])
