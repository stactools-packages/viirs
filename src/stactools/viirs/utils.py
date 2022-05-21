import warnings
from typing import List, cast

import rasterio
from rasterio.errors import NotGeoreferencedWarning


def subdatasets(href: str) -> List[str]:
    """Returns a list of HDF file subdatasets.

    Includes a warning-catcher so you don't get a "no CRS" warning while doing it.

    Args:
        href (str): HREF to a VIIRS H5 file.

    Returns:
        List[str]: A list of subdatasets (GDAL-openable paths)
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
        with rasterio.open(href) as dataset:
            return cast(List[str], dataset.subdatasets)


def version_string(version: str) -> str:
    if version == "1":
        return "001"
    else:
        raise ValueError(f"Unsupported VIIRS version: {version}")
