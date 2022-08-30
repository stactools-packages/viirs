import os
from typing import Any, Dict, List, Optional, Tuple, cast

import h5py
import numpy as np
import rasterio
import rasterio.shutil
from rasterio.io import MemoryFile

from stactools.viirs.constants import MULTIPLE_NODATA
from stactools.viirs.metadata import viirs_metadata
from stactools.viirs.utils import ignore_not_georeferenced

COG_PROFILE = {"compress": "deflate", "blocksize": 512, "driver": "COG"}


@ignore_not_georeferenced()
def cogify(infile: str, outdir: str) -> List[str]:
    """Creates COGs for the provided HDF5 file.

    COGs are created using h5py as the data reader to avoid rasterio and/or GDAL
    silently converting int8 (signed byte) data to uint8 (byte).

    Args:
        infile (str): The input H5 file
        outdir (str): The output directory

    Returns:
        List[str]: The COG hrefs
    """
    metadata = viirs_metadata(infile)
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

        with rasterio.open(rasterio_subdataset_path, "r") as tag_src:
            rasterio_tags = tag_src.tags()

        with h5py.File(infile) as h5:
            data: Any = np.array(h5[subdataset_key])
            if len(data.shape) == 1:  # skip single value (non-data) "grids"
                continue
            if len(data.shape) == 3:
                raise ValueError(
                    f"MultiBand COG creation not supported for {metadata.product}"
                )

            # gdal (and software built on gdal) doesn't always play well with signed byte data
            data = np.int16(data) if data.dtype == "int8" else data

            temp = None
            if "_FillValue" in h5[subdataset_key].attrs.keys():
                temp = h5[subdataset_key].attrs["_FillValue"].item()
            elif "_Fillvalue" in h5[subdataset_key].attrs.keys():
                temp = h5[subdataset_key].attrs["_Fillvalue"].item()
            nodata = None if temp == b"n/a" else temp

            multiple = MULTIPLE_NODATA.get(metadata.product, {}).get(
                subdataset_name, None
            )
            if multiple:
                nodatas = cast(List[int], multiple["multiple"])
                nodata_new = cast(int, multiple["new"])
                clean_data, clean_nodata = _clean(data, nodatas, nodata_new)
                nodata_cog_path = f"{os.path.splitext(cog_path)[0]}_fill.tif"
                _cog(
                    clean_data,
                    metadata.crs,
                    metadata.transform,
                    rasterio_tags,
                    cog_path,
                    nodata_new,
                )
                cog_paths.append(cog_path)
                _cog(
                    clean_nodata,
                    metadata.crs,
                    metadata.transform,
                    rasterio_tags,
                    nodata_cog_path,
                    nodata_new,
                )
                cog_paths.append(nodata_cog_path)
            else:
                _cog(
                    data,
                    metadata.crs,
                    metadata.transform,
                    rasterio_tags,
                    cog_path,
                    nodata,
                )
                cog_paths.append(cog_path)

    return cog_paths


def _cog(
    data: Any,
    crs: str,
    transform: List[float],
    tags: Dict[str, Any],
    cog_path: str,
    nodata: Optional[int] = None,
) -> None:
    src_profile = dict(
        driver="GTiff",
        dtype=data.dtype,
        nodata=nodata,
        count=1,
        height=data.shape[0],
        width=data.shape[1],
        crs=crs,
        transform=rasterio.Affine(*transform),
    )

    with MemoryFile() as mem_file:
        with mem_file.open(**src_profile) as mem:
            mem.write(data, 1)
            mem.update_tags(**tags)
            rasterio.shutil.copy(mem, cog_path, **COG_PROFILE)


def _clean(data: Any, nodatas: List[int], nodata_new: int) -> Tuple[Any, Any]:
    np.ma.asarray(data)
    for nodata in nodatas:
        data = np.ma.masked_equal(data, nodata)
    clean_data = np.ma.filled(data, nodata_new)

    mask = np.ma.getmaskarray(data)
    clean_nodata = np.ma.getdata(data)
    clean_nodata[~mask] = nodata_new

    return (clean_data, clean_nodata)
