import ast
import datetime
import logging
import os.path
import warnings
from typing import Callable, List, Optional, cast

import fsspec
import h5py
import rasterio
import shapely.geometry
from dateutil import parser
from lxml import etree
from rasterio.errors import NotGeoreferencedWarning
from shapely.geometry import Polygon
from stactools.core.io import ReadHrefModifier
from stactools.core.io.xml import XmlElement
from stactools.core.utils import href_exists

from stactools.viirs import constants

logger = logging.getLogger(__name__)


class MissingElement(Exception):
    """An expected element is missing from the XML file"""


class Metadata:
    """Structure to hold values from a metadata XML file or other metadata source.

    XML metadata is preferred since it is consistent between products. Metadata
    from the H5 file attributes will be used if an XML file does not exist.
    Since neither the XML file or H5 attributes contain all required
    information, we also look inside the EOS Metadata Structure in the H5 file.
    """

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
        self.xml_href = self._xml_href(read_href_modifier)

        if read_href_modifier:
            self.read_h5_href = read_href_modifier(h5_href)
        else:
            self.read_h5_href = h5_href

        if self.xml_href:
            self._from_xml()
        else:
            self._from_h5_attributes()
        self._hdfeos_metadata()

        self.subdatasets = self._subdatasets()

    def _from_xml(self) -> None:
        def missing_element(attribute: str) -> Callable[[str], Exception]:
            def get_exception(xpath: str) -> Exception:
                return MissingElement(
                    f"Could not find attribute `{attribute}` at xpath "
                    f"'{xpath}' at href {self.xml_href}"
                )

            return get_exception

        with fsspec.open(self.read_xml_href) as file:
            root = XmlElement(etree.parse(file, base_url=self.xml_href).getroot())

        metadata = root.find_or_throw(
            "GranuleURMetaData", missing_element("URMetadata")
        )
        self.id = os.path.splitext(
            metadata.find_text_or_throw(
                "ECSDataGranule/LocalGranuleID", missing_element("id")
            )
        )[0]
        self.product = metadata.find_text_or_throw(
            "CollectionMetaData/ShortName", missing_element("product")
        )
        version = metadata.find_text_or_throw(
            "CollectionMetaData/VersionID", missing_element("version")
        )
        if version == "1":
            self.version = "001"
        else:
            raise ValueError(f"Unsupported VIIRS version: {version}")

        points = [
            (
                float(
                    point.find_text_or_throw(
                        "PointLongitude", missing_element("longitude")
                    )
                ),
                float(
                    point.find_text_or_throw(
                        "PointLatitude", missing_element("latitude")
                    )
                ),
            )
            for point in metadata.findall(
                "SpatialDomainContainer/HorizontalSpatialDomainContainer/"
                "GPolygon/Boundary/Point"
            )
        ]
        polygon = Polygon(points)
        self.geometry = shapely.geometry.mapping(polygon)
        self.bbox = polygon.bounds

        start_date = metadata.find_text_or_throw(
            "RangeDateTime/RangeBeginningDate", missing_element("start_date")
        )
        start_time = metadata.find_text_or_throw(
            "RangeDateTime/RangeBeginningTime", missing_element("start_time")
        )
        self.start_datetime = datetime.datetime.fromisoformat(
            f"{start_date}T{start_time}"
        )
        end_date = metadata.find_text_or_throw(
            "RangeDateTime/RangeEndingDate", missing_element("end_date")
        )
        end_time = metadata.find_text_or_throw(
            "RangeDateTime/RangeEndingTime", missing_element("end_time")
        )
        self.end_datetime = datetime.datetime.fromisoformat(f"{end_date}T{end_time}")

        self.created_datetime = datetime.datetime.fromisoformat(
            metadata.find_text_or_throw(
                "ECSDataGranule/ProductionDateTime", missing_element("created")
            )
        )
        self.updated_datetime = datetime.datetime.fromisoformat(
            metadata.find_text_or_throw("LastUpdate", missing_element("updated"))
        )

        psas = metadata.findall("PSAs/PSA")
        for psa in psas:
            name = psa.find_text_or_throw("PSAName", missing_element("PSAName"))
            value = psa.find_text_or_throw("PSAValue", missing_element("PSAValue"))
            if name == "HORIZONTALTILENUMBER":
                self.horizontal_tile = int(value)
            elif name == "VERTICALTILENUMBER":
                self.vertical_tile = int(value)
            elif name == "TileID":
                self.tile_id = value

        self.cloud_cover = None

    def _from_h5_attributes(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(self.read_h5_href) as dataset:
                tags = dataset.tags()
                tags = {k.lower(): v for k, v in tags.items()}

        self.id = os.path.splitext(tags["localgranuleid"])[0]
        self.product: str = tags["shortname"]
        self.version = tags["versionid"]

        latitudes = tags.get("gringlatitude", None) or tags.get(
            "gringpointlatitude", None
        )
        longitudes = tags.get("gringlongitude", None) or tags.get(
            "gringpointlongitude", None
        )
        latitudes = latitudes.strip().split(" ")
        longitudes = longitudes.strip().split(" ")
        points = [(float(lon), float(lat)) for lon, lat in zip(longitudes, latitudes)]
        polygon = Polygon(points)
        self.geometry = shapely.geometry.mapping(polygon)
        self.bbox = polygon.bounds

        self.start_datetime = parser.parse(tags["starttime"])
        self.end_datetime = parser.parse(tags["endtime"])
        self.created_datetime = parser.parse(tags["productiontime"])
        self.updated_datetime = None

        self.horizontal_tile = int(tags["horizontaltilenumber"])
        self.vertical_tile = int(tags["verticaltilenumber"])
        self.tile_id = tags["tileid"]

        cloud_cover = tags.get("hdfeos_grids_percentcloud", None)
        self.cloud_cover = float(cloud_cover) if cloud_cover else cloud_cover

    def _hdfeos_metadata(self) -> None:
        with h5py.File(self.read_h5_href, "r") as h5:
            metadata_str = (
                h5["HDFEOS INFORMATION"]["StructMetadata.0"][()].decode("utf-8").strip()
            )
            metadata_split_str = [m.strip() for m in metadata_str.split("\n")]
            metadata_keys_values = [s.split("=") for s in metadata_split_str][:-1]
            metadata_dict = {key: value for key, value in metadata_keys_values}
            grid_attributes = h5["HDFEOS"]["GRIDS"].attrs.items()
            grid_attributes_dict = {k.lower(): v for k, v in grid_attributes}

        split_str = [m.strip() for m in metadata_str.split("\n")]
        metadata_keys_values = [s.split("=") for s in split_str][:-1]
        metadata_dict = {key: value for key, value in metadata_keys_values}

        # XDim = #rows, YDim = #Columns. Seems backwards. But correct per
        # https://lpdaac.usgs.gov/data/get-started-data/collection-overview/
        # missions/s-npp-nasa-viirs-overview/
        self.shape = [int(metadata_dict["XDim"]), int(metadata_dict["YDim"])]
        self.left, self.top = ast.literal_eval(metadata_dict["UpperLeftPointMtrs"])

        if self.cloud_cover is None:
            cloud_cover = grid_attributes_dict.get("percentcloud", None)
            self.cloud_cover = float(cloud_cover) if cloud_cover else cloud_cover

    def _xml_href(
        self, read_href_modifier: Optional[ReadHrefModifier]
    ) -> Optional[str]:
        xml_href = f"{self.h5_href}.xml"

        if read_href_modifier:
            self.read_xml_href = read_href_modifier(xml_href)
        else:
            self.read_xml_href = xml_href

        if href_exists(self.read_xml_href):
            return xml_href
        else:
            return None

    def _subdatasets(self) -> List[str]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(self.read_h5_href) as dataset:
                return cast(List[str], dataset.subdatasets)

    @property
    def collection(self) -> str:
        return self.product[3:]

    @property
    def transform(self) -> List[float]:
        if self.shape[0] == 1200:
            spatial_resolution = constants.BINSIZE_1000M
        elif self.shape[0] == 2400:
            spatial_resolution = constants.BINSIZE_500M
        elif self.shape[0] == 3000:
            spatial_resolution = constants.BINSIZE_375M
        return [spatial_resolution, 0.0, self.left, 0.0, -spatial_resolution, self.top]

    @property
    def wkt2(self) -> str:
        return constants.WKT2_METERS

    @property
    def epsg(self) -> None:
        return None
