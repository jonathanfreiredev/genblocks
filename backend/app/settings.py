from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Defaults to production so a missing ENV never silently enables
    # development-only behaviour (SQL echo, text logs). Set ENV=development locally.
    env: str = "production"
    database_url: str
    # Base URL of the frontend, used to build the links sent to the user.
    frontend_url: str = "http://localhost:3000"
    # Minimum level for the application logs (DEBUG, INFO, WARNING, ...).
    log_level: str = "INFO"
    # Base URL of the Supabase project that issues the access tokens. The issuer
    # and the JWKS endpoint are derived from it (see the properties below).
    supabase_url: str
    # Audience claim Supabase access tokens carry.
    supabase_jwt_audience: str = "authenticated"
    # Public URL of the MCP server, as its clients reach it. Published as the
    # protected resource in the OAuth discovery document, so it must be the URL
    # clients use, not a container-internal hostname.
    mcp_base_url: str = "http://localhost:8001"
    # Where this service reaches the MCP server as a client (the playground). It
    # is a different address from ``mcp_base_url`` inside compose, where the
    # service answers to its own name rather than to localhost.
    mcp_internal_url: str = "http://localhost:8001"
    # Comma-separated list of browser origins allowed to call the API. Set the
    # real frontend domain(s) in production.
    cors_origins: str = "http://localhost:3000"

    @property
    def debug(self) -> bool:
        return self.env == "development"

    @property
    def cors_origin_list(self) -> list[str]:
        """Allowed browser origins, split from the comma-separated setting."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def mcp_internal_endpoint(self) -> str:
        """The full URL of the MCP endpoint this service calls as a client."""
        return f"{self.mcp_internal_url.rstrip('/')}/mcp"

    @property
    def supabase_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_issuer}/.well-known/jwks.json"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
