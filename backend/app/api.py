from fastapi import APIRouter

from app.demo.router import demo_router
from app.organizations.router import organizations_router
from app.users.router import users_router

# Versioned entrypoint for the application API. Add new routers here; the whole
# surface is mounted under ``/v1`` from ``app/main.py``. Infrastructure routes
# (health checks) stay unversioned on purpose.
api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(users_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(demo_router)
