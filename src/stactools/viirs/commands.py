import logging
import os
from typing import Optional

import click
from click import Command, Group
from stactools.core.utils.antimeridian import Strategy

from stactools.viirs import cog, stac

logger = logging.getLogger(__name__)


def create_viirs_command(cli: Group) -> Command:
    """Creates the stactools-viirs command line utility."""

    @cli.group(
        "viirs",
        short_help=("Commands for working with stactools-viirs"),
    )
    def viirs() -> None:
        pass

    @viirs.command("create-cogs", short_help="Create subdataset COGs")
    @click.argument("INFILE")
    @click.option("-o", "--outdir", help="directory for COG file")
    def create_cogs(infile: str, outdir: Optional[str]) -> None:
        """Creates a COG for each subdataset in an H5 file.

        \b
        Args:
            infile (str): HREF to a VIIRS H5 file
            outdir (str): The directory that will contain the COGs. The default
                is the H5 directory.
        """
        if outdir is None:
            outdir = os.path.dirname(infile)
        cog.cogify(infile, outdir)

        return None

    @viirs.command("create-item", short_help="Create a STAC Item")
    @click.argument("INFILE")
    @click.argument("OUTDIR")
    @click.option(
        "-a",
        "--antimeridian_strategy",
        type=click.Choice(["normalize", "split"], case_sensitive=False),
        default="split",
        show_default=True,
        help="geometry strategy for antimeridian scenes",
    )
    @click.option(
        "-c",
        "--cogify",
        is_flag=True,
        help="Convert the H5 subdatasets into COGs",
        default=False,
    )
    @click.option(
        "-d",
        "--densify_factor",
        help="Factor by which to densify the Item geometry",
        type=int,
    )
    @click.option(
        "-f", "--file-list", help="File containing list of subdataset COG HREFs"
    )
    def create_item_command(
        infile: str,
        outdir: str,
        antimeridian_strategy: str,
        cogify: bool,
        densify_factor: Optional[int] = None,
        file_list: Optional[str] = None,
    ) -> None:
        """Creates a STAC Item based on an H5 VIIRS data file and, if it exists,
        the corresponding XML metadata file.

        \b
        Args:
            infile (str): The source H5 file.
            outdir (str): Directory that will contain the STAC Item.
            antimeridian_strategy (str, optional): Choice of 'normalize' or
                'split' to either split the Item geometry on -180 longitude or
                normalize the Item geometry so all longitudes are either
                positive or negative. Default is 'split'.
            cogify (bool, optional): Flag to create COGS from the subdatasets in
                the H5 file. The COGs will saved alongside the H5 file. COGs
                will not be created if the file_list option is also supplied.
            file_list (str, optional): Text file containing one HREF per line.
                The HREFs should point to subdataset COG files.
        """
        strategy = Strategy[antimeridian_strategy.upper()]

        hrefs = None
        if file_list:
            with open(file_list) as file:
                hrefs = [line.strip() for line in file.readlines()]
        elif cogify:
            h5dir = os.path.dirname(infile)
            hrefs = cog.cogify(infile, h5dir)

        item = stac.create_item(
            infile,
            cog_hrefs=hrefs,
            antimeridian_strategy=strategy,
            densify_factor=densify_factor,
        )
        item_path = os.path.join(outdir, f"{item.id}.json")
        item.set_self_href(item_path)
        item.make_asset_hrefs_relative()
        item.validate()
        item.save_object()

        return None

    return viirs
