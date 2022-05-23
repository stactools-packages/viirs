import json
from typing import Any, Dict

import pkg_resources
from pystac import Asset, Extent, Link, MediaType, Provider


class STACFragments:
    """Class for accessing collection and asset data."""

    def __init__(self, product: str) -> None:
        self.product = product

    def assets(self):
        self.assets = self._load("assets.json")

    def subdataset_asset(self, subdataset: str) -> Asset:
        subdataset_asset = self.assets[subdataset]
        subdataset_asset["type"] = MediaType.COG
        return subdataset_asset

    def collection(self) -> Dict[str, Any]:
        data = self._load("collection.json")
        data["extent"] = Extent.from_dict(data["extent"])
        data["providers"] = [
            Provider.from_dict(provider) for provider in data["providers"]
        ]
        data["links"] = [Link.from_dict(link) for link in data["links"]]
        return data

    def _load(self, file_name: str) -> Any:
        try:
            with pkg_resources.resource_stream(
                    "stactools.viirs.fragments",
                    f"fragments/{self.product}/{file_name}") as stream:
                return json.load(stream)
        except FileNotFoundError as e:
            raise e
