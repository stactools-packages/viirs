from pystac import MediaType

CLASSIFICATION_EXTENSION_HREF = ("https://stac-extensions.github.io/"
                                 "classification/v1.0.0/schema.json")
HDF5_ASSET_KEY = "hdf5"
HDF5_ASSET_PROPERTIES = {
    "type": MediaType.HDF5,
    "roles": ["data"],
    "title": "Source data containing all bands"
}
METADATA_ASSET_KEY = "metadata"
METADATA_ASSET_PROPERTIES = {
    "type": MediaType.XML,
    "roles": ["metadata"],
    "title": "Earth Observing System Data and Information System (EOSDIS) metadata"
}
