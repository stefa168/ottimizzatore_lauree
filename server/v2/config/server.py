from pydantic import BaseModel


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    keepalive: int = 65
    reload: bool = False
    reload_dirs: list[str] = ["app"]
