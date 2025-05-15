import binascii
import os

from advanced_alchemy.utils.text import slugify
from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    # app_loc: str = "v2.asgi:create_app"
    url: str = "http://localhost:8000"
    debug: bool = False
    secret_key: str = Field(default_factory=lambda: binascii.hexlify(os.urandom(32)).decode(encoding="utf-8"))
    name: str = "app"
    allowed_cors_origins: list[str] = ["*"]

    # csrf_cookie_name: str = "XSRF-TOKEN"
    # csrf_cookie_secure: bool = False

    @property
    def slug(self) -> str:
        """Return a slugified name."""
        return slugify(self.name)



