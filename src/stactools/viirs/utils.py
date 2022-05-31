import warnings
from typing import List, Optional, cast

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


def subdataset_dtype(href: str, sanitized_path):
    print(sanitized_path)
    unsanitized_names = []
    with h5py.File(href) as h5:
        h5.visit(lambda key : unsanitized_names.append(key) if isinstance(h5[key], h5py.Dataset) else None)

        sanitary_unsanitary = {}
        for unsanitized_name in unsanitized_names:
            sanitized = unsanitized_name.replace(" ", "_")
            sanitary_unsanitary[sanitized] = unsanitized_name

        import json
        # print(json.dumps(sanitary_unsanitary, indent=4))

        subdataset = h5[sanitary_unsanitary[sanitized_path]]
        data_type = subdataset.dtype
        # data_type = "int16" if data_type == "int8" else data_type
    
    # print(data_type)
    return data_type


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
