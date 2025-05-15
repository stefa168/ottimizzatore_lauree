from __future__ import annotations

import json
import os
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field
from litestar.config.cors import CORSConfig

from v2.config.app import AppSettings
from v2.config.db import DatabaseSettings
from v2.config.log_settings import LogSettings
from v2.config.server import ServerSettings


class Settings(BaseModel):
    app: AppSettings = AppSettings()
    db: DatabaseSettings
    server: ServerSettings = ServerSettings()
    log: LogSettings = LogSettings()

    @classmethod
    def from_yaml(cls, path: Path) -> Settings:
        with path.open("r") as file:
            config_data = yaml.safe_load(file)
            return Settings(**config_data)

    @property
    def cors_config(self) -> CORSConfig:
        return CORSConfig(allow_origins=self.app.allowed_cors_origins)


def save_schema_to_file(p: Path):
    schema = Settings.model_json_schema()
    with p.open("w") as f:
        # noinspection PyTypeChecker
        json.dump(schema, f, indent=2)
    print(f"JSON Schema saved to {p}")


if __name__ == '__main__':
    save_schema_to_file(Path(os.getcwd()) / "schema.json")
