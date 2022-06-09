from pystac import MediaType

PLATFORMS = {"VNP": "snpp"}

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

EPSG = {"VNP46A2": "EPSG:4326"}
SINUSOIDAL_WKT2 = 'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid",6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'  # noqa

CLASSIFICATION_EXTENSION_HREF = (
    "https://stac-extensions.github.io/" "classification/v1.0.0/schema.json"
)

MULTIPLE_NODATA = {
    "VNP13A1": {
        "500_m_16_days_EVI": {"multiple": [-15000, -13000], "new": -32768},
        "500_m_16_days_EVI2": {"multiple": [-15000, -13000], "new": -32768},
        "500_m_16_days_NDVI": {"multiple": [-15000, -13000], "new": -32768},
        "500_m_16_days_pixel_reliability": {"multiple": [-1, -4], "new": -32768},
    },
    "VNP15A2H": {
        "Fpar": {"multiple": [249, 250, 251, 252, 253, 254, 255], "new": 200},
        "Lai": {"multiple": [249, 250, 251, 252, 253, 254, 255], "new": 200},
        "FparStdDev": {
            "multiple": [248, 249, 250, 251, 252, 253, 254, 255],
            "new": 200,
        },
        "LaiStdDev": {"multiple": [248, 249, 250, 251, 252, 253, 254, 255], "new": 200},
    },
    "VNP10A1": {
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
