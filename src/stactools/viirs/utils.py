import warnings
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from pystac.extensions.eo import EOExtension
from pystac.extensions.raster import RasterExtension
from rasterio.errors import NotGeoreferencedWarning
from stactools.core.io import ReadHrefModifier

from stactools.viirs import constants


@contextmanager
def ignore_not_georeferenced() -> Generator[None, None, None]:
    """Suppress rasterio's warning when opening a dataset that contains no
    georeferencing information.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
        yield


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


def find_extensions(assets: Dict[str, Any]) -> List[str]:
    """Adds extensions to the Item extension list if they exist on the Item assets.

    NOTE: This package does not nest the classification extension inside
    'raster:bands', so we do not check for its existence there.

    Args:
        item (Item): The Item being modified
    """
    extensions = set()
    for asset in assets.values():
        if "classification:classes" in asset or "classification:bitfields" in asset:
            extensions.add(constants.CLASSIFICATION_EXTENSION_HREF)
        if "eo:bands" in asset:
            extensions.add(EOExtension.get_schema_uri())
        if "raster:bands" in asset:
            extensions.add(RasterExtension.get_schema_uri())

    return list(extensions)
