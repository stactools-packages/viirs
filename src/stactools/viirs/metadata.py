import ast
import logging
import os.path
import warnings
from typing import List, Optional, cast

import h5py
import rasterio
import shapely.geometry
from dateutil import parser
from rasterio.errors import NotGeoreferencedWarning
from shapely.geometry import Polygon
from stactools.core.io import ReadHrefModifier
from stactools.core.utils import href_exists

from stactools.viirs import constants

logger = logging.getLogger(__name__)


class Metadata:
    """Structure to hold values fetched from a metadata XML file or other metadata source."""

    def __init__(
        self, h5_href: str, read_href_modifier: Optional[ReadHrefModifier] = None
    ):
        """Read metadata from the first h5 dataset and the xml metadata file.

        Args:
            href (str): The href of the xml metadata file
            read_href_modifier (Optional[Callable[[str], str]]): Optional
                function to modify the read href
        """
        self.h5_href = h5_href
        self.read_href_modifier = read_href_modifier

        if read_href_modifier:
            self.read_h5_href = read_href_modifier(h5_href)
        else:
            self.read_h5_href = self.h5_href

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(self.read_h5_href) as dataset:
                self.tags = dataset.tags()
                self.subdatasets = cast(List[str], dataset.subdatasets)

        self._h5_attributes()
        self._hdfeos_metadata()

    def _h5_attributes(self) -> None:
        self.id = os.path.splitext(self.tags["LocalGranuleID"])[0]
        self.product: str = self.tags["ShortName"]
        self.version = self.tags["VersionID"]

        latitudes = self.tags["GRingLatitude"].strip().split(" ")
        longitudes = self.tags["GRingLongitude"].strip().split(" ")
        points = [(float(lon), float(lat)) for lon, lat in zip(longitudes, latitudes)]
        polygon = Polygon(points)
        self.geometry = shapely.geometry.mapping(polygon)
        self.bbox = polygon.bounds

        self.start_datetime = parser.parse(self.tags["StartTime"])
        self.end_datetime = parser.parse(self.tags["EndTime"])
        self.created_datetime = parser.parse(self.tags["ProductionTime"])

        self.horizontal_tile = int(self.tags["HorizontalTileNumber"])
        self.vertical_tile = int(self.tags["VerticalTileNumber"])
        self.tile_id = self.tags["TileID"]

        self.cloud_cover = float(self.tags["HDFEOS_GRIDS_PercentCloud"])

    def _hdfeos_metadata(self) -> None:
        with h5py.File(self.read_h5_href, "r") as h5:
            file_metadata = h5["HDFEOS INFORMATION"]["StructMetadata.0"][()].split()
        metadata = [m.decode("utf-8") for m in file_metadata]
        metadata_keys_values = [s.split("=") for s in metadata][:-1]
        metadata_dict = {key: value for key, value in metadata_keys_values}

        # XDim = #rows, YDim = #Columns per https://lpdaac.usgs.gov/data/get-started-data/collection-overview/missions/s-npp-nasa-viirs-overview/  # noqa
        self.shape = [int(metadata_dict["XDim"]), int(metadata_dict["YDim"])]
        self.left, self.top = ast.literal_eval(metadata_dict["UpperLeftPointMtrs"])

    @property
    def collection(self) -> str:
        return self.product[3:]

    @property
    def transform(self) -> List[float]:
        px_size = constants.SPATIAL_RESOLUTION[self.product]
        return [px_size, 0.0, self.left, 0.0, -px_size, self.top]

    @property
    def wkt2(self) -> str:
        return constants.WKT2[self.product]

    @property
    def epsg(self) -> None:
        return None

    @property
    def xml_href(self) -> Optional[str]:
        xml_href = f"{self.h5_href}.xml"
        if self.read_href_modifier:
            read_xml_href = self.read_href_modifier(xml_href)
        else:
            read_xml_href = xml_href

        if href_exists(read_xml_href):
            return xml_href
        else:
            logger.debug(f"No xml file found for h5 file: {self.h5_href}")
            return None
