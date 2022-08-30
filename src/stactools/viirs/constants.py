from enum import Enum

from pystac import MediaType


class VIIRSProducts(str, Enum):
    VNP09A1 = "VNP09A1"
    VNP09H1 = "VNP09H1"
    VNP10A1 = "VNP10A1"
    VNP13A1 = "VNP13A1"
    VNP14A1 = "VNP14A1"
    VNP15A2H = "VNP15A2H"
    VNP21A2 = "VNP21A2"
    VNP43IA4 = "VNP43IA4"
    VNP43MA4 = "VNP43MA4"
    VNP46A2 = "VNP46A2"


FOOTPRINT_DENSIFICATION_FACTOR = 10
FOOTPRINT_SIMPLIFICATION_TOLERANCE = 0.0006  # degrees; approximately 60m
FOOTPRINT_PRECISION = 7

PLATFORM = "snpp"
INSTRUMENT = ["viirs"]

HDF5_ASSET_KEY = "hdf5"
HDF5_ASSET_PROPERTIES = {
    "type": MediaType.HDF5,
    "roles": ["data"],
    "title": "Source Data Containing All Bands",
}
METADATA_ASSET_KEY = "metadata"
METADATA_ASSET_PROPERTIES = {
    "type": MediaType.XML,
    "roles": ["metadata"],
    "title": "Earth Observing System Data and Information System (EOSDIS) Metadata",
}

EPSG = {VIIRSProducts.VNP46A2.name: "EPSG:4326"}
SINUSOIDAL_WKT2 = 'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid",6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'  # noqa

CLASSIFICATION_EXTENSION_HREF = (
    "https://stac-extensions.github.io/classification/v1.0.0/schema.json"
)

# fmt: off
MULTIPLE_NODATA = {
    VIIRSProducts.VNP13A1.name: {
        "500_m_16_days_EVI": {
            "multiple": [-15000, -13000],
            "new": -32768
        },
        "500_m_16_days_EVI2": {
            "multiple": [-15000, -13000],
            "new": -32768
        },
        "500_m_16_days_NDVI": {
            "multiple": [-15000, -13000],
            "new": -32768
        },
        "500_m_16_days_pixel_reliability": {
            "multiple": [-1, -4],
            "new": -32768
        },
    },
    VIIRSProducts.VNP15A2H.name: {
        "Fpar": {
            "multiple": [249, 250, 251, 252, 253, 254, 255],
            "new": 200
        },
        "Lai": {
            "multiple": [249, 250, 251, 252, 253, 254, 255],
            "new": 200
        },
        "FparStdDev": {
            "multiple": [248, 249, 250, 251, 252, 253, 254, 255],
            "new": 200,
        },
        "LaiStdDev": {
            "multiple": [248, 249, 250, 251, 252, 253, 254, 255],
            "new": 200
        },
    },
    VIIRSProducts.VNP10A1.name: {
        "NDSI": {
            "multiple": [21100, 23900, 25100, 25200, 25300, 25400],
            "new": 32767,  # per spec
        },
        "NDSI_Snow_Cover": {
            "multiple": [201, 211, 237, 239, 250, 251, 253, 254],
            "new": 255,  # per spec
        },
    },
}
# fmt: on
