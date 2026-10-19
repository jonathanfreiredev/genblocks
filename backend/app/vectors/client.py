"""The vector store: one client, two collections.

Retrieval is what lets the registry answer "have we built this already?" and
"have we photographed this already?" — questions a search over titles cannot
answer, because two blocks can be named differently and be the same idea.

Development runs on a local persistent client (a directory, no server); production
points at Chroma Cloud with the four settings it needs. The choice is made here
once, so nothing downstream knows which one it is talking to.
"""

import chromadb
from chromadb.api import ClientAPI

from app.settings import settings

# The two kinds of thing the registry remembers. Components are embedded from their
# render, images from the picture itself: the vector is of the artifact, not of the
# words somebody wrapped it in.
COMPONENTS = "components"
IMAGES = "images"

# Cosine, so a distance is 1 - similarity and the thresholds mean the same thing
# whichever collection they are read from.
SPACE = {"hnsw:space": "cosine"}

_client: ClientAPI | None = None


def client() -> ClientAPI:
    """The store, connected once per process."""
    global _client

    if _client is None:
        _client = _connect()

    return _client


def collection(name: str):
    """One collection, created on first use with the metric retrieval assumes."""
    return client().get_or_create_collection(name=name, metadata=SPACE)


def _connect() -> ClientAPI:
    """Chroma Cloud when it is configured, a directory when it is not."""
    if settings.chroma_api_key and settings.chroma_tenant and settings.chroma_database:
        return chromadb.CloudClient(
            api_key=settings.chroma_api_key,
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
        )

    if settings.chroma_host:
        return chromadb.HttpClient(
            host=settings.chroma_host,
            ssl=True,
            headers={"x-chroma-token": settings.chroma_api_key or ""},
            tenant=settings.chroma_tenant or None,
            database=settings.chroma_database or None,
        )

    return chromadb.PersistentClient(path=settings.chroma_path)
