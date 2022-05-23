import os
from typing import List, Tuple

from stactools.core.utils.subprocess import call

from stactools.viirs import constants
from stactools.viirs.metadata import Metadata


def cogify(infile: str, outdir: str) -> Tuple[List[str], List[str]]:
    """Creates cogs for the provided H5 file.

    Args:
        infile (str): The input H5 file
        outdir (str): The output directory

    Returns:
        Tuple[List[str], List[str]]: A two tuple (paths, names):
            - The first element is a list of the output tif paths
            - The second element is a list of subdataset names
    """
    metadata = Metadata(infile)
    subdatasets = metadata.subdatasets
    base_file_name = os.path.splitext(os.path.basename(infile))[0]
    paths = []
    subdataset_names = []
    for subdataset in subdatasets:
        parts = subdataset.split(":")
        subdataset_path = parts[-1]
        parts = subdataset_path.split("/")
        subdataset_name = parts[-1]
        sanitized_subdataset_name = subdataset_name.replace(" ", "_")
        file_name = f"{base_file_name}_{sanitized_subdataset_name}.tif"
        outfile = os.path.join(outdir, file_name)

        px_size = constants.SPATIAL_RESOLUTION[metadata.product]
        height, width = metadata.shape
        ulx = metadata.left
        uly = metadata.top
        lrx = ulx + px_size * width
        lry = uly - px_size * height

        args = [
            "gdal_translate",
            "-of",
            "COG",
            "-a_srs",
            f"{metadata.wkt2}",
            "-a_ullr",
            f"{ulx}",
            f"{uly}",
            f"{lrx}",
            f"{lry}",
            "-co",
            "compress=deflate",
            "-co",
            "blocksize=512",
            f"{subdataset}",
            f"{outfile}",
        ]
        call(args)

        subdataset_names.append(sanitized_subdataset_name)
        paths.append(outfile)

    return (paths, subdataset_names)
