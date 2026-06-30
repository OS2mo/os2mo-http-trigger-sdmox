# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, PositiveInt, root_validator
from pydantic.main import BaseModel
from pydantic.tools import parse_obj_as
from pydantic.types import SecretStr

from app.pydantic_types import Domain, Port


class AMQPTLS(BaseModel):
    username: str
    password: SecretStr
    ca: bytes
    cert: bytes
    key: bytes


class Settings(BaseSettings):
    mora_url: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "https://moradev.magentahosted.dk")
    saml_token: Optional[UUID] = None

    triggered_uuids: List[UUID]
    ou_levelkeys: List[str]

    amqp_username: str
    amqp_password: str
    amqp_host: Domain = Domain("msg-amqp.silkeborgdata.dk")
    amqp_virtual_host: str
    amqp_port: Port = Port(5672)
    amqp_check_waittime: PositiveInt = PositiveInt(3)
    amqp_check_retries: PositiveInt = PositiveInt(6)
    # If true, the new AQMP TLS system will be used.
    # TODO: remove flag once we have seen the new system work. The flag is necessary for
    #       now, since we would like to manually test the new AMQP system with a CLI
    #       (or something)
    amqp_use_tls: bool = False
    amqp_tls: AMQPTLS | None = None

    sd_username: str
    sd_password: str
    sd_institution: str
    sd_base_url: HttpUrl = parse_obj_as(HttpUrl, "https://service.sd.dk/sdws/")

    jaeger_service: str = "SDMox"
    jaeger_hostname: Optional[str] = None
    jaeger_port: Port = Port(6831)

    class Config:
        env_nested_delimiter = "__"

    @root_validator
    def ensure_amqp_tls(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values["amqp_use_tls"] and values["amqp_tls"] is None:
            raise ValueError("AMQP TLS settings are missing!")
        return values


def get_settings(**overrides) -> Settings:
    return Settings(**overrides)
