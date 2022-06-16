import json
from typing import Any, Dict, Optional

import pkg_resources
from pystac import Extent, Link, MediaType, Provider


class STACFragments:
    """Class for accessing collection and asset data."""

    def __init__(self, product: str, production_year_doy: int = 2999000) -> None:
        # If a production date is not supplied, we would like to default to
        # generating the most up-to-date assets. The default value is therefore
        # set far into the future (year 2999, day 000) so that all asset
        # updates are applied when a production_year_doy is not supplied.
        self.product = product
        self.item = self._load("item.json")
        self.assets = self.item["assets"]
        if "asset-updates" in self.item:
            self._update_assets(production_year_doy)

    def gsd(self) -> Optional[int]:
        """Returns the Item Ground Sample Distance (GSD).

        Returns:
            Optional[int]: GSD in meters
        """
        gsd: Optional[int] = self.item.get("gsd", None)
        return gsd

    def assets_dict(self) -> Dict[str, Any]:
        """Returns a dictionary of Asset dictionaries (less the 'href' field)
        for the VIIRS product used to create the class instance.

        Returns:
            Dict[str, Any]: Dictionary of Asset dictionaries
        """
        assets: Dict[str, Any] = self.assets
        for key in assets.keys():
            assets[key]["type"] = MediaType.COG
        return assets

    def subdataset_dict(self, subdataset: str) -> Dict[str, Any]:
        """Returns an Asset dictionary (less the 'href' field) for the given
        product subdataset.

        Args:
            subdataset (str): Subdataset name (from H5 file)

        Returns:
            Dict[str, Any]: Asset dictionary
        """
        subdataset_asset: Dict[str, Any] = self.assets[subdataset]
        subdataset_asset["type"] = MediaType.COG
        return subdataset_asset

    def collection_dict(self) -> Dict[str, Any]:
        """Returns a dictionary of Collection fields (not exhaustive) for the
        VIIRS product used to create the class instance.

        Returns:
            Dict[str, Any]: Dictionary of Collection fields
        """
        collection: Dict[str, Any] = self._load("collection.json")
        collection["extent"] = Extent.from_dict(collection["extent"])
        collection["providers"] = [
            Provider.from_dict(provider) for provider in collection["providers"]
        ]
        collection["links"] = [Link.from_dict(link) for link in collection["links"]]
        return collection

    def _update_assets(self, production_year_doy: int) -> None:
        def update_fields(source: Dict[str, Any], updates: Dict[str, Any]) -> None:
            for band, fields in updates.items():
                for field, value in fields.items():
                    source[band][field] = value

        asset_updates = self.item["asset-updates"]
        for update_year_doy, bands in asset_updates.items():
            if production_year_doy >= int(update_year_doy):
                update_fields(self.assets, bands)

    def _load(self, file_name: str) -> Any:
        try:
            with pkg_resources.resource_stream(
                "stactools.viirs.fragment", f"fragments/{self.product}/{file_name}"
            ) as stream:
                return json.load(stream)
        except FileNotFoundError as e:
            raise e
