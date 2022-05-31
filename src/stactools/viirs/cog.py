import warnings
import os
from typing import List, Tuple

import numpy as np
import h5py
import rasterio
from rasterio.io import MemoryFile
from rasterio.errors import NotGeoreferencedWarning
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import stactools.core.utils.convert

from stactools.viirs.metadata import viirs_metadata
from stactools.viirs import utils


# def cogify(infile: str, outdir: str) -> Tuple[List[str], List[str]]:
#     """Creates cogs for the provided H5 file.

#     Args:
#         infile (str): The input H5 file
#         outdir (str): The output directory

#     Returns:
#         Tuple[List[str], List[str]]: A two tuple (paths, names):
#             - The first element is a list of the output tif paths
#             - The second element is a list of subdataset names
#     """
#     metadata = viirs_metadata(infile)
#     subdatasets = utils.subdatasets(infile)
#     base_file_name = os.path.splitext(os.path.basename(infile))[0]
#     paths = []
#     subdataset_names = []
#     for subdataset in subdatasets:
#         parts = subdataset.split(":")
#         subdataset_path = parts[-1]
#         h5_filepath = parts[-2]

#         parts = subdataset_path.split("/")
#         subdataset_name = parts[-1]
#         sanitized_subdataset_name = subdataset_name.replace(" ", "_")
#         file_name = f"{base_file_name}_{sanitized_subdataset_name}.tif"
#         outfile = os.path.join(outdir, file_name)

#         # data_type = utils.subdataset_dtype(h5_filepath, subdataset_path.strip("/"))

#         px_size = metadata.spatial_resolution
#         height, width = metadata.shape
#         ulx = metadata.left
#         uly = metadata.top
#         lrx = ulx + px_size * width
#         lry = uly - px_size * height

#         args = [
#             "gdal_translate",
#             "-strict",
#             "-of",
#             "COG",
#             "-a_srs",
#             f"{metadata.wkt2}",
#             "-a_ullr",
#             f"{ulx}",
#             f"{uly}",
#             f"{lrx}",
#             f"{lry}",
#             "-co",
#             "compress=deflate",
#             # "-co",
#             # "tiled=YES",
#             # "-co",
#             # "blockxsize=512"
#             "-co",
#             "blocksize=512",
#             "-co",
#             "pixeltype=signedbyte",
#             f"{subdataset}",
#             f"{outfile}",
#         ]
#         call(args)

#         subdataset_names.append(sanitized_subdataset_name)
#         paths.append(outfile)

#     return (paths, subdataset_names)


# def cogify(infile: str, outdir: str) -> Tuple[List[str], List[str]]:
#     """Creates cogs for the provided HDF file.
#     Args:
#         infile (str): The input HDF file
#         outdir (str): The output directory
#     Returns:
#         Tuple[List[str], List[str]]: A two tuple (paths, names):
#             - The first element is a list of the output tif paths
#             - The second element is a list of subdataset names
#     """
#     subdatasets = utils.subdatasets(infile)
#     base_file_name = os.path.splitext(os.path.basename(infile))[0]
#     paths = []
#     subdataset_names = []
#     for subdataset in subdatasets:
#         parts = subdataset.split(":")
#         subdataset_path = parts[-1]
#         parts = subdataset_path.split("/")
#         subdataset_name = parts[-1]
#         sanitized_subdataset_name = subdataset_name.replace(" ", "_")
#         subdataset_names.append(sanitized_subdataset_name)
#         file_name = f"{base_file_name}_{sanitized_subdataset_name}.tif"
#         outfile = os.path.join(outdir, file_name)
#         stactools.core.utils.convert.cogify(subdataset, outfile)
#         paths.append(outfile)
#     return (paths, subdataset_names)


# def cogify(infile: str, outdir: str) -> Tuple[List[str], List[str]]:
#     """Creates cogs for the provided HDF file.
#     Args:
#         infile (str): The input HDF file
#         outdir (str): The output directory
#     Returns:
#         Tuple[List[str], List[str]]: A two tuple (paths, names):
#             - The first element is a list of the output tif paths
#             - The second element is a list of subdataset names
#     """
#     metadata = Metadata.from_h5(infile)
#     subdatasets = utils.subdatasets(infile)
#     base_file_name = os.path.splitext(os.path.basename(infile))[0]
#     paths = []
#     subdataset_names = []
#     for subdataset in subdatasets:
#         parts = subdataset.split(":")
#         subdataset_path = parts[-1]
#         h5_filepath = parts[-2]

#         parts = subdataset_path.split("/")
#         subdataset_name = parts[-1]
#         sanitized_subdataset_name = subdataset_name.replace(" ", "_")
#         subdataset_names.append(sanitized_subdataset_name)
#         file_name = f"{base_file_name}_{sanitized_subdataset_name}.tif"
#         outfile = os.path.join(outdir, file_name)
        
#         data_type = utils.subdataset_dtype(h5_filepath, subdataset_path.strip("/"))

#         import rasterio
#         with rasterio.open(subdataset, "r") as src:
#             data = src.read(1)
#             with rasterio.open(
#                 outfile, "w",
#                 driver = "COG",
#                 height = metadata.shape[0],
#                 width=metadata.shape[1],
#                 count=1,
#                 transform = metadata.transform,
#                 crs = metadata.wkt2,
#                 dtype=data_type
#             ) as dst:
#                 dst.write(data, 1)

#         stactools.core.utils.convert.cogify(subdataset, outfile)
#         paths.append(outfile)
#     return (paths, subdataset_names)


def cogify(infile: str, outdir: str) -> List[str]:
    """Creates COGs for the provided HDF5 file.

    Args:
        infile (str): The input HDF5 file
        outdir (str): The output directory

    Returns:
        List[str]: The COG hrefs
    """
    metadata = viirs_metadata(infile)
    base_filename = os.path.splitext(os.path.basename(infile))[0]

    all_keys = []
    with h5py.File(infile) as h5:
        h5.visit(all_keys.append)
        subdataset_keys = [key for key in all_keys if isinstance(h5[key], h5py.Dataset) and "GRIDS" in key]

    cog_paths = []
    for key in subdataset_keys:
        sanitized_key = key.replace(" ", "_")
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
            dataset = h5[key]
            data = np.array(dataset)
            # if data.dtype == "int8":
            #     data = np.int16(data)

            src_profile = dict(
                driver="GTiff",
                dtype=data.dtype,
                count=1,
                height=data.shape[0],
                width=data.shape[1],
                crs=metadata.wkt2,
                transform=rasterio.Affine(*metadata.transform)
            )

            with MemoryFile() as mem_file:
                with mem_file.open(**src_profile) as mem:
                    mem.write(data, 1)
                    mem.update_tags(**rasterio_tags)
                    stactools.core.utils.convert.cogify(mem, cog_path)

        cog_paths.append(cog_path)

    return cog_paths