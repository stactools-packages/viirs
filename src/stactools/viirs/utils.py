import warnings
from typing import Any, Dict, List, cast

import h5py
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
            # print(dataset.tags()["HDFEOS_GRIDS_PercentCloud"])
            td = dataset.tags()
            for item in td.items():
                print(item)
            print(dataset.subdatasets)
            return cast(List[str], dataset.subdatasets)


def h5_metadata(href: str) -> Dict[str, Any]:
    with h5py.File(href, "r") as h5:
        file_metadata = h5['HDFEOS INFORMATION']['StructMetadata.0'][()].split()
        file_attributes = list(h5.attrs.items())

    metadata = [m.decode('utf-8') for m in file_metadata]
    metadata_keys_values = [s.split("=") for s in metadata][:-1]
    metadata_dict = {key: value for key, value in metadata_keys_values}

    for key, value in file_attributes:
        if isinstance(value, bytes):
            _value = value.decode("utf-8")
        else:
            _value = value
        metadata_dict[key] = _value

    return metadata_dict



def version_string(version: str) -> str:
    if version == "1":
        return "001"
    else:
        raise ValueError(f"Unsupported VIIRS version: {version}")