import ast
import re
import datetime
import os.path
from typing import Callable, Optional, cast, List
import logging

import fsspec
import shapely.geometry
from lxml import etree
from shapely.geometry import Polygon
from stactools.core.io import ReadHrefModifier
from stactools.core.io.xml import XmlElement
import rasterio
from stactools.core.utils import href_exists
import h5py

from stactools.viirs import utils, constants

logger = logging.getLogger(__name__)


class MissingElement(Exception):
    """An expected element is missing from the XML file"""


class Metadata:
    """Structure to hold values fetched from a metadata XML file or other metadata source."""

    def __init__(self, h5_href:str, read_href_modifier: Optional[ReadHrefModifier] = None):
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

        with rasterio.open(self.read_h5_href) as dataset:
            self.tags = dataset.tags()
            self.subdatasets = cast(List[str], dataset.subdatasets)
        if not self.subdatasets:
            raise ValueError(
                f"No subdatasets found in H5 file: {h5_href}")

        self._h5_attributes()
        self._h5_metadata()

    def _h5_attributes(self):
        self.id = os.path.splitext(self.tags["LocalGranuleID"])[0]
        self.product = self.tags["ShortName"]
        self.version = self.tags["VersionID"]
        
        latitudes = self.tags["GRingLatitude"].split(" ")[0:-1]
        longitudes = self.tags["GRingLongitude"].split(" ")[0:-1]
        print(latitudes)
        print(longitudes)
        points = [(float(lon), float(lat)) for lon, lat in zip(longitudes, latitudes)]
        polygon = Polygon(points)
        self.geometry = shapely.geometry.mapping(polygon)
        self.bbox = polygon.bounds

        def clean_time(date_time: str):
            date_reg = re.compile(r"\d{4}-\d{2}-\d{2}")
            time_reg = re.compile(r"\d{2}:\d{2}:\d{2}\.\d*")
            if date_reg.search(date_time):
                date_str = date_reg.group()
            if time_reg.search(date_time):
                time_str = time_reg.group()
            return datetime.datetime.fromisoformat(f"{date_str}T{time_str}")

        h5_start_datetime = self.tags["StartTime"]
        h5_end_datetime = self.tags["EndTime"]
        h5_production_datetime = self.tags["ProductionTime"]
        self.start_datetime = clean_time(h5_start_datetime)
        self.end_datetime = clean_time(h5_end_datetime)
        self.created_datetime = clean_time(h5_production_datetime)

        self.horizontal_tile = int(self.tags["HorizontalTileNumber"])
        self.vertical_tile = int(self.tags["VerticalTileNumber"])
        self.tile_id = self.tags["TileID"]

        self.cloud_cover = float(self.tags["HDFEOS_GRIDS_PercentCloud"])

    def _h5_metadata(self):
        with h5py.File(self.read_h5_href, "r") as h5:
            file_metadata = h5['HDFEOS INFORMATION']['StructMetadata.0'][()].split()
        metadata = [m.decode('utf-8') for m in file_metadata]
        metadata_keys_values = [s.split("=") for s in metadata][:-1]
        metadata_dict = {key: value for key, value in metadata_keys_values}

        self.shape = (int(metadata_dict["YDim"]), int(metadata_dict["XDim"]))
        self.upper_left = ast.literal_eval(metadata_dict["UpperLeftPointMtrs"])

    @property
    def collection(self) -> str:
        return self.product[3:]
    
    @property
    def transform(self) -> List[float]:
        left, upper = self.upper_left
        px_size = constants.SPATIAL_RESOLUTION[self.product]
        return [px_size, 0.0, left, 0.0, -px_size, upper]

    @staticmethod
    def wkt2() -> str:
        return constants.WKT2["self.product"]

    @staticmethod
    def epsg() -> None:
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