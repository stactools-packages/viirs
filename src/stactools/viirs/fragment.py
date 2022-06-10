import json
from typing import Any, Dict

import pkg_resources
from pystac import Extent, Link, MediaType, Provider


class STACFragments:
    """Class for accessing collection and asset data."""

    def __init__(self, product: str) -> None:
        self.product = product

    def load_assets(self) -> None:
        self.assets = self._load("assets.json")

    def assets_dict(self) -> Dict[str, Any]:
        assets: Dict[str, Any] = self.assets
        for key in assets.keys():
            assets[key]["type"] = MediaType.COG
        return assets

    def subdataset_dict(self, subdataset: str) -> Any:
        subdataset_asset = self.assets[subdataset]
        subdataset_asset["type"] = MediaType.COG
        return subdataset_asset

    def collection_dict(self) -> Dict[str, Any]:
        collection: Dict[str, Any] = self._load("collection.json")
        collection["extent"] = Extent.from_dict(collection["extent"])
        collection["providers"] = [
            Provider.from_dict(provider) for provider in collection["providers"]
        ]
        collection["links"] = [Link.from_dict(link) for link in collection["links"]]
        return collection

    def _load(self, file_name: str) -> Any:
        try:
            with pkg_resources.resource_stream(
                "stactools.viirs.fragment", f"fragments/{self.product}/{file_name}"
            ) as stream:
                return json.load(stream)
        except FileNotFoundError as e:
            raise e
