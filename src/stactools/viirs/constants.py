from enum import Enum, auto

from pystac import MediaType


class VIIRSProducts(Enum):
    VNP09A1 = auto()
    VNP09H1 = auto()
    VNP10A1 = auto()
    VNP13A1 = auto()
    VNP14A1 = auto()
    VNP15A2H = auto()
    VNP21A2 = auto()
    VNP43IA4 = auto()
    VNP43MA4 = auto()
    VNP46A2 = auto()


PLATFORM = "snpp"
INSTRUMENT = ["viirs"]

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

EPSG = {VIIRSProducts.VNP46A2.name: "EPSG:4326"}
SINUSOIDAL_WKT2 = 'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid",6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'  # noqa

CLASSIFICATION_EXTENSION_HREF = (
    "https://stac-extensions.github.io/" "classification/v1.0.0/schema.json"
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
