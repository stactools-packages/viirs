from enum import Enum, auto

from pystac import MediaType


class Products(Enum):
    VNP09H1 = auto()


CLASSIFICATION_EXTENSION_HREF = (
    "https://stac-extensions.github.io/" "classification/v1.0.0/schema.json"
)
HDF5_ASSET_KEY = "hdf5"
HDF5_ASSET_PROPERTIES = {
    "type": MediaType.HDF5,
    "roles": ["data"],
    "title": "Source data containing all bands",
}
METADATA_ASSET_KEY = "metadata"
METADATA_ASSET_PROPERTIES = {
    "type": MediaType.XML,
    "roles": ["metadata"],
    "title": "Earth Observing System Data and Information System (EOSDIS) metadata",
}

BINSIZE_500M = 463.313
BINSIZE_1000M = 926.625
SPATIAL_RESOLUTION = {Products.VNP09H1.name: BINSIZE_500M}

WKT2_METERS = 'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid",6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'  # noqa
WKT2 = {Products.VNP09H1.name: WKT2_METERS}
