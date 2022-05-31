import ast
import warnings
from typing import List, Optional, Tuple, cast

import h5py
import rasterio
from pystac import Item
from pystac.extensions.eo import EOExtension
from pystac.extensions.raster import RasterExtension
from rasterio.errors import NotGeoreferencedWarning
from stactools.core.io import ReadHrefModifier

from stactools.viirs import constants


def subdatasets(href: str) -> List[str]:
    """Returns a list of subdatasets from this HDF file href.

    Includes a warning-catcher so you don't get a "no CRS" warning while doing it.

    Args:
        href (str): The HREF to a VIIRS H5 file.

    Returns:
        List[str]: A list of subdatasets (GDAL-openable paths)
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
        with rasterio.open(href) as dataset:
            return cast(List[str], dataset.subdatasets)


def modify_href(
    href: str, read_href_modifier: Optional[ReadHrefModifier] = None
) -> str:
    """Generate a modified href, e.g., add a token to a url.

    Args:
        href (str): The HREF to be modified
        read_href_modifier (ReadHrefModifier): function that modifies an HREF
    """
    if read_href_modifier:
        read_href = read_href_modifier(href)
        return read_href
    else:
        return href


def add_extensions(item: Item) -> None:
    """Adds extensions to the Item extension list if they exist on the Item assets.

    Args:
        item (Item): The Item being modified
    """
    item_str = str(item.to_dict())

    if "classification:classes" in item_str or "classification:bitfields" in item_str:
        item.stac_extensions.append(constants.CLASSIFICATION_EXTENSION_HREF)
    if "eo:bands" in item_str:
        EOExtension.add_to(item)
    if "raster:bands" in item_str:
        RasterExtension.add_to(item)

    return None


def hdfeos_metadata(h5_href: str) -> Tuple[List[int], float, float]:
    """Extracts spatial metadata from the EOS metadata structure of an H5 file.

    Args:
        h5_href (str): HREF to the h5 file

    Returns:
        Tuple[List[int], Tuple[float]]:
            - Height and width of the data arrays stored in the H5 file
            - Projected coordinates of the left, top corner of the data
    """
    with h5py.File(h5_href, "r") as h5:
        metadata_str = (
            h5["HDFEOS INFORMATION"]["StructMetadata.0"][()].decode("utf-8").strip()
        )
        metadata_split_str = [m.strip() for m in metadata_str.split("\n")]
        metadata_keys_values = [s.split("=") for s in metadata_split_str][:-1]
        metadata_dict = {key: value for key, value in metadata_keys_values}

    # XDim = #rows, YDim = #columns per https://lpdaac.usgs.gov/data/get-started-data/collection-overview/missions/s-npp-nasa-viirs-overview/  # noqa
    shape = [int(metadata_dict["XDim"]), int(metadata_dict["YDim"])]
    assert shape[0] == shape[1]
    left, top = ast.literal_eval(metadata_dict["UpperLeftPointMtrs"])

    return (shape, left, top)


def transform(shape: List[int], left: float, top: float) -> List[float]:
    """Creates elements of a geospatial transform matrix.

    Args:
        shape (List[float]): List containing the array height and width
        left (float): Left projected coordinate of the top-left corner
        top (float): Top projected coordinate of the top-lef corner

    Returns:
        List[float]: First six elements of the transformation matrix

    """
    if shape[0] == 1200:
        pixel_size = constants.BINSIZE_1000M
    elif shape[0] == 2400:
        pixel_size = constants.BINSIZE_500M
    elif shape[0] == 3000:
        pixel_size = constants.BINSIZE_375M
    return [pixel_size, 0.0, left, 0.0, -pixel_size, top]
