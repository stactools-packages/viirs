import warnings
from typing import List, Optional, cast

import rasterio
from pystac import Item
from pystac.extensions.eo import EOExtension
from pystac.extensions.raster import RasterExtension
from rasterio.errors import NotGeoreferencedWarning
from stactools.core.io import ReadHrefModifier

from stactools.viirs import constants


def subdatasets(href: str) -> List[str]:
    """Returns a list of subdatasets from this HDF file href.

    Includes a warning-cathcher so you don't get a "no CRS" warning while doing it.

    Args:
        href (str): The HREF to a MODIS HDF file.

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
    """Generate a modified href, e.g. to add a token to a url."""
    if read_href_modifier:
        read_href = read_href_modifier(href)
        return read_href
    else:
        return href


def add_extensions(item: Item) -> None:
    for asset in item.assets.values():
        asset_dict = asset.to_dict()
        if (
            "classification:classes" in asset_dict
            or "classification:bitfields" in asset_dict
        ):
            item.stac_extensions.append(constants.CLASSIFICATION_EXTENSION_HREF)
        if "eo:bands" in asset_dict:
            EOExtension.add_to(item)
        if "raster:bands" in asset_dict:
            RasterExtension.add_to(item)
    item.stac_extensions = list(set(item.stac_extensions))
