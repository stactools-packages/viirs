import logging
from typing import Optional
import os

import click
from click import Command, Group

from stactools.viirs import stac, cog

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
    @click.option("-o", "--outdir", help="directory for COG files")
    def create_cogs(infile: str, outdir: Optional[str]) -> None:
        """Creates a COG for each subdataset in an HDF5 file.

        \b
        Args:
            infile (str): HREF to a VIIRS HDF5 file
            outdir (Optional[str]): Optional directory for the COGs; default is
                to save the COGs to the same directory as the HDF5 file.
        """
        if outdir is None:
            outdir = os.path.dirname(infile)
        paths, subdataset_names = cog.cogify(infile, outdir)

        for path, subdataset_name in zip(paths, subdataset_names):
            print(f"Subdataset '{subdataset_name}' COG saved to {path}")

        return None

    @viirs.command("create-item", short_help="Create a STAC Item")
    @click.argument("INFILE")
    @click.argument("OUTDIR")
    @click.option(
        "-c",
        "--cogify",
        is_flag=True,
        help="Convert the HDF5 subdatasets into COGs",
        default=False,
    )
    def create_item_command(infile: str, outdir: str, cogify: bool) -> None:
        """Creates a STAC Item based on metadata from an .hdf.xml MODIS file.

        \b
        Args:
            infile (str): The source HDF5 file. A .h5.xml metadata file is
                expected to reside alongside the .h5 source file.
            outdir (str): Directory that will contain the STAC Item.
            cogify (bool, optional): Convert the .h5 file into multiple
                Cloud-Optimized GeoTIFFs, one per subdataset. The COGs will
                saved alongside the .h5 file.
        """
        paths = None
        if cogify:
            h5dir = os.path.dirname(infile)
            paths, subdataset_names = cog.cogify(infile, h5dir)
        item = stac.create_item(infile, cog_hrefs=paths)
        item_path = os.path.join(outdir, "{}.json".format(item.id))
        item.set_self_href(item_path)
        item.validate()
        item.save_object()

        return None

    return viirs

    # @viirs.command(
    #     "create-collection",
    #     short_help="Creates a STAC collection",
    # )
    # @click.argument("destination")
    # def create_collection_command(destination: str) -> None:
    #     """Creates a STAC Collection

    #     Args:
    #         destination (str): An HREF for the Collection JSON
    #     """
    #     collection = stac.create_collection()

    #     collection.set_self_href(destination)

    #     collection.save_object()

    #     return None
