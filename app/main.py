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

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from os2mo_fastapi_utils.tracing import setup_instrumentation, setup_logging

from app.config import get_settings
from app.routers import api, trigger_api

tags_metadata = [
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


app.include_router(api.router, tags=["API"])
app.include_router(trigger_api.router, prefix="/triggers", tags=["Trigger API"])

app = setup_instrumentation(app)
setup_logging()
