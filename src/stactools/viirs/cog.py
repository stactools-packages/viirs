import os
import warnings
from typing import Any, List

import h5py
import numpy as np
import rasterio
import stactools.core.utils.convert
from rasterio.errors import NotGeoreferencedWarning
from rasterio.io import MemoryFile

from stactools.viirs import constants, utils


def cogify(infile: str, outdir: str) -> List[str]:
    """Creates COGs for the provided HDF5 file.

    Args:
        infile (str): The input HDF5 file
        outdir (str): The output directory

    Returns:
        List[str]: The COG hrefs
    """
    shape, left, top = utils.hdfeos_metadata(infile)
    transform = utils.transform(shape, left, top)
    base_filename = os.path.splitext(os.path.basename(infile))[0]

    all_keys: List[str] = []
    with h5py.File(infile) as h5:
        h5.visit(all_keys.append)
        subdataset_keys = [
            key
            for key in all_keys
            if isinstance(h5[key], h5py.Dataset) and "GRIDS" in key
        ]

    cog_paths = []
    for subdataset_key in subdataset_keys:
        sanitized_key = subdataset_key.replace(" ", "_")
        rasterio_subdataset_path = f"HDF5:{infile}://{sanitized_key}"

        parts = sanitized_key.split("/")
        subdataset_name = parts[-1]
        cog_filename = f"{base_filename}_{subdataset_name}.tif"
        cog_path = os.path.join(outdir, cog_filename)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(rasterio_subdataset_path, "r") as tag_src:
                rasterio_tags = tag_src.tags()

        with h5py.File(infile) as h5:
            data: Any = np.array(h5[subdataset_key])
            if len(data.shape) == 1:  # skip single value (non-data) "grids"
                continue
            data = np.int16(data) if data.dtype == "int8" else data

            src_profile = dict(
                driver="GTiff",
                dtype=data.dtype,
                count=1,
                height=data.shape[0],
                width=data.shape[1],
                crs=constants.WKT2,
                transform=rasterio.Affine(*transform),
            )

            with MemoryFile() as mem_file:
                with mem_file.open(**src_profile) as mem:
                    mem.write(data, 1)
                    mem.update_tags(**rasterio_tags)
                    stactools.core.utils.convert.cogify(mem, cog_path)

        cog_paths.append(cog_path)

    return cog_paths
