import warnings
from typing import List, Optional, cast

import rasterio
from rasterio.errors import NotGeoreferencedWarning
from stactools.core.io import ReadHrefModifier


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
