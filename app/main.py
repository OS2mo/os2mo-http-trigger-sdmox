# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
#
# Triggerkoden i dette modul har to funktioner:
# 1) At oprette/rette/flytte en afdeling i SD, inden det sker i OS2mo.
# 2) At forhinde oprettelse/flytning/rettelse i OS2mo, hvis det ikke lykkedes i SD.
#
# Adressernes rækkefølge har betydning.
#
# Der skal findes en postadresse inden man opretter et PNummer,
# ellers går tilbagemeldingen fra SD tilsyneladende i ged.
# - Der er indført et check for det i sd_mox.py

import sys

sys.path.insert(0, "/")

from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from structlog.processors import KeyValueRenderer

from app.config import get_settings
from app.routers import api, trigger_api
from app.sd_mox import SDMoxError
from app.sd_tree_org import department_identifier_list, sd_tree_org

tags_metadata: List[Dict[str, Any]] = [
    {
        "name": "Meta",
        "description": "Various meta endpoints",
    },
    {
        "name": "API",
        "description": "Direct API for end-users.",
    },
    {
        "name": "Trigger API",
        "description": "Trigger API for mo-triggers.",
        "externalDocs": {
            "description": "OS2MO Trigger docs",
            "url": "https://os2mo.readthedocs.io/en/development/api/triggers.html",
        },
    },
]

app = FastAPI(
    title="SDMox",
    description="API to make changes in SD.",
    version="0.0.1",
    openapi_tags=tags_metadata,
)


@app.on_event("startup")
async def startup_event():
    # Called for validation side-effect
    get_settings()


@app.get(
    "/", response_class=RedirectResponse, tags=["Meta"], summary="Redirect to /docs"
)
def root() -> RedirectResponse:
    """Redirect to /docs."""
    return RedirectResponse(url="/docs")


@app.get("/info", tags=["Meta"], summary="Print info about this entity")
def info() -> Dict[str, Any]:
    """Print info about this entity."""
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
    }


@app.get(
    "/tree",
    tags=["Meta"],
    summary="Printout org tree from SD",
    response_class=PlainTextResponse,
)
async def tree(root_uuid: Optional[UUID] = None) -> str:
    return await sd_tree_org(root_uuid)


@app.get(
    "/duplicates",
    tags=["Meta"],
    summary="Printout Department Identifiers with duplicates from SD",
    response_class=JSONResponse,
)
async def duplicates() -> Dict[str, int]:
    return await department_identifier_list()


@app.exception_handler(SDMoxError)
async def sdmox_exception_handler(request: Request, exc: SDMoxError):
    return JSONResponse(
        status_code=422,
        content={"detail": f"{str(exc)}"},
    )


from pika.exceptions import ProbableAuthenticationError


@app.exception_handler(ProbableAuthenticationError)
async def pika_exception_handler(request: Request, exc: ProbableAuthenticationError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"SDMOX Miskonfiguration: {str(exc)}"},
    )


from aiohttp.client_exceptions import ClientResponseError


@app.exception_handler(ClientResponseError)
async def aiohttp_exception_handler(request: Request, exc: ClientResponseError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"SDMOX Miskonfiguration: {str(exc)}"},
    )


from requests.exceptions import RequestException


@app.exception_handler(RequestException)
async def requests_exception_handler(request: Request, exc: RequestException):
    return JSONResponse(
        status_code=500,
        content={"detail": f"SDMOX Miskonfiguration: {str(exc)}"},
    )


app.include_router(api.router, tags=["API"])
app.include_router(trigger_api.router, prefix="/triggers", tags=["Trigger API"])

from structlog.contextvars import merge_contextvars

structlog.configure(processors=[merge_contextvars, KeyValueRenderer()])
