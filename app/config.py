# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, PositiveInt, root_validator
from pydantic.main import BaseModel
from pydantic.tools import parse_obj_as
from pydantic.types import SecretStr

from app.pydantic_types import Port


class AMQPTLS(BaseModel):
    host: str
    port: int
    server: str
    virtual_host: str
    username: str
    password: SecretStr
    ca: bytes
    cert: bytes
    key: bytes
    exchange: str


class Settings(BaseSettings):
    mora_url: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "https://moradev.magentahosted.dk")
    saml_token: Optional[UUID] = None

    triggered_uuids: List[UUID]
    ou_levelkeys: List[str]

    amqp_check_waittime: PositiveInt = PositiveInt(3)
    amqp_check_retries: PositiveInt = PositiveInt(6)
    amqp_tls: AMQPTLS

    sd_username: str
    sd_password: str
    sd_institution: str
    sd_base_url: HttpUrl = parse_obj_as(HttpUrl, "https://service.sd.dk/sdws/")

    jaeger_service: str = "SDMox"
    jaeger_hostname: Optional[str] = None
    jaeger_port: Port = Port(6831)

    class Config:
        env_nested_delimiter = "__"


def get_settings(**overrides) -> Settings:
    return Settings(**overrides)
