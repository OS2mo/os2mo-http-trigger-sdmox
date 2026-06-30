# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

import sys

sys.path.insert(0, "/")

import json

import click

from app.sd_mox import SDMox
from app.util import async_to_sync, first_of_month

clickDate = click.DateTime(formats=["%Y-%m-%d"])


@click.group()
@click.option(
    "--from-date",
    type=clickDate,
    default=str(first_of_month()),
    help="TODO",
    show_default=True,
)
@click.option("--overrides", multiple=True)
@click.pass_context
def sd_mox_cli(ctx, from_date, overrides):
    """Tool to make changes in SD."""

    from_date = from_date.date()

    overrides = dict(override.split("=") for override in overrides)

    sdmox = SDMox(from_date, overrides=overrides)

    ctx.ensure_object(dict)
    ctx.obj["sdmox"] = sdmox
    ctx.obj["from_date"] = from_date


@sd_mox_cli.command()
@click.pass_context
@click.option("--unit-uuid", type=click.UUID, required=True)
@click.option("--print-department", is_flag=True, default=False)
@click.option("--unit-name")
@async_to_sync
async def check_name(ctx, unit_uuid, print_department, unit_name):
    mox = ctx.obj["sdmox"]

    unit_uuid = str(unit_uuid)
    department, errors = await mox._check_department(
        unit_uuid=unit_uuid,
        unit_name=unit_name,
    )
    if print_department:
        print(json.dumps(department, indent=4))

    if errors:
        click.echo("Mismatches found for:")
        for error in errors:
            click.echo("* " + click.style(error, fg="red"))


@sd_mox_cli.command()
@click.pass_context
@click.option("--unit-uuid", type=click.UUID, required=True)
@click.option("--new-unit-name")
@click.option("--dry-run", is_flag=True, default=False)
@async_to_sync
async def set_name(ctx, unit_uuid, new_unit_name, dry_run):
    unit_uuid = str(unit_uuid)

    mox = ctx.obj["sdmox"]
    await mox.rename_unit(
        unit_uuid, new_unit_name, at=ctx.obj["from_date"], dry_run=dry_run
    )


@sd_mox_cli.command()
@click.pass_context
async def test_amqp_connection(ctx):
    """
    Test the AMQP connection.

    To the new SD AMQP TLS system, run this CLI with
    $ AMQP_USE_TLS=true python -m app.cli test_amqp_connection
    """
    mox = ctx.obj["sdmox"]
    mox._amqp_connect()


if __name__ == "__main__":
    sd_mox_cli()
