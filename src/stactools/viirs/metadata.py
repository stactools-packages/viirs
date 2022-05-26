import ast
import datetime
import logging
import os.path
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

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
from stactools.viirs.utils import modify_href

logger = logging.getLogger(__name__)


class MissingElement(Exception):
    """An expected element is missing from the XML file"""


@dataclass
class Metadata:
    """Structure to hold values from a metadata XML file or source H5 file.

    XML metadata is preferred since it is consistent between products.
    Neither an XML metadata file nor the H5 source file attributes contain all
        required information; additional information is extracted from the EOS
        Metadata Structure in the H5 file whether using an XML or H5 file as the
        primary metadata source.
    """

    id: str
    product: str
    version: str
    geometry: Dict[str, Any]
    bbox: List[float]
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    created_datetime: datetime.datetime
    updated_datetime: Optional[datetime.datetime]
    horizontal_tile: int
    vertical_tile: int
    tile_id: str
    shape: List[int]
    left: float
    top: float
    xml_href: Optional[str]

    @classmethod
    def from_xml_and_h5(
        cls, h5_href: str, read_href_modifier: Optional[ReadHrefModifier] = None
    ) -> "Metadata":
        """Extracts metadata from XML elements and H5 EOS metadata structure"""

        def missing_element(attribute: str) -> Callable[[str], Exception]:
            def get_exception(xpath: str) -> Exception:
                return MissingElement(
                    f"Could not find attribute `{attribute}` at xpath "
                    f"'{xpath}' at href {xml_href}"
                )

            return get_exception

        xml_href = f"{h5_href}.xml"
        read_xml_href = modify_href(xml_href, read_href_modifier)
        read_h5_href = modify_href(h5_href, read_href_modifier)

        with fsspec.open(read_xml_href) as file:
            root = XmlElement(etree.parse(file, base_url=xml_href).getroot())

        metadata = root.find_or_throw(
            "GranuleURMetaData", missing_element("URMetadata")
        )
        id = os.path.splitext(
            metadata.find_text_or_throw(
                "ECSDataGranule/LocalGranuleID", missing_element("id")
            )
        )[0]
        product = metadata.find_text_or_throw(
            "CollectionMetaData/ShortName", missing_element("product")
        )
        version = metadata.find_text_or_throw(
            "CollectionMetaData/VersionID", missing_element("version")
        )
        if version == "1":
            version = "001"
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
        geometry = shapely.geometry.mapping(polygon)
        bbox = polygon.bounds

        start_date = metadata.find_text_or_throw(
            "RangeDateTime/RangeBeginningDate", missing_element("start_date")
        )
        start_time = metadata.find_text_or_throw(
            "RangeDateTime/RangeBeginningTime", missing_element("start_time")
        )
        start_datetime = datetime.datetime.fromisoformat(f"{start_date}T{start_time}")
        end_date = metadata.find_text_or_throw(
            "RangeDateTime/RangeEndingDate", missing_element("end_date")
        )
        end_time = metadata.find_text_or_throw(
            "RangeDateTime/RangeEndingTime", missing_element("end_time")
        )
        end_datetime = datetime.datetime.fromisoformat(f"{end_date}T{end_time}")

        created_datetime = datetime.datetime.fromisoformat(
            metadata.find_text_or_throw(
                "ECSDataGranule/ProductionDateTime", missing_element("created")
            )
        )
        updated_datetime = datetime.datetime.fromisoformat(
            metadata.find_text_or_throw("LastUpdate", missing_element("updated"))
        )

        psas = metadata.findall("PSAs/PSA")
        for psa in psas:
            name = psa.find_text_or_throw("PSAName", missing_element("PSAName"))
            value = psa.find_text_or_throw("PSAValue", missing_element("PSAValue"))
            if name == "HORIZONTALTILENUMBER":
                horizontal_tile = int(value)
            elif name == "VERTICALTILENUMBER":
                vertical_tile = int(value)
            elif name == "TileID":
                tile_id = value

        shape, left, top = cls._hdfeos_metadata(read_h5_href)

        return Metadata(
            id=id,
            product=product,
            version=version,
            geometry=geometry,
            bbox=bbox,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            created_datetime=created_datetime,
            updated_datetime=updated_datetime,
            horizontal_tile=horizontal_tile,
            vertical_tile=vertical_tile,
            tile_id=tile_id,
            shape=shape,
            left=left,
            top=top,
            xml_href=xml_href,
        )

    @classmethod
    def from_h5(
        cls, h5_href: str, read_href_modifier: Optional[ReadHrefModifier] = None
    ) -> "Metadata":
        """Extracts metadata from H5 attributes and H5 EOS metadata structure"""
        read_h5_href = modify_href(h5_href, read_href_modifier)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(read_h5_href) as dataset:
                tags = dataset.tags()
                tags = {k.lower(): v for k, v in tags.items()}

        id = os.path.splitext(tags["localgranuleid"])[0]
        product: str = tags["shortname"]
        version = tags["versionid"]

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
        geometry = shapely.geometry.mapping(polygon)
        bbox = polygon.bounds

        start_datetime = parser.parse(tags["starttime"])
        end_datetime = parser.parse(tags["endtime"])
        created_datetime = parser.parse(tags["productiontime"])

        horizontal_tile = int(tags["horizontaltilenumber"])
        vertical_tile = int(tags["verticaltilenumber"])
        tile_id = tags["tileid"]

        shape, left, top = cls._hdfeos_metadata(read_h5_href)

        return Metadata(
            id=id,
            product=product,
            version=version,
            geometry=geometry,
            bbox=bbox,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            created_datetime=created_datetime,
            updated_datetime=None,
            horizontal_tile=horizontal_tile,
            vertical_tile=vertical_tile,
            tile_id=tile_id,
            shape=shape,
            left=left,
            top=top,
            xml_href=None,
        )

    @staticmethod
    def _hdfeos_metadata(read_h5_href: str) -> Any:
        with h5py.File(read_h5_href, "r") as h5:
            metadata_str = (
                h5["HDFEOS INFORMATION"]["StructMetadata.0"][()].decode("utf-8").strip()
            )
            metadata_split_str = [m.strip() for m in metadata_str.split("\n")]
            metadata_keys_values = [s.split("=") for s in metadata_split_str][:-1]
            metadata_dict = {key: value for key, value in metadata_keys_values}

        split_str = [m.strip() for m in metadata_str.split("\n")]
        metadata_keys_values = [s.split("=") for s in split_str][:-1]
        metadata_dict = {key: value for key, value in metadata_keys_values}

        # XDim = #rows, YDim = #columns per https://lpdaac.usgs.gov/data/get-started-data/collection-overview/missions/s-npp-nasa-viirs-overview/  # noqa
        shape = [int(metadata_dict["XDim"]), int(metadata_dict["YDim"])]
        left, top = ast.literal_eval(metadata_dict["UpperLeftPointMtrs"])

        return shape, left, top

    @property
    def transform(self) -> List[float]:
        spatial_resolution = self.spatial_resolution
        return [spatial_resolution, 0.0, self.left, 0.0, -spatial_resolution, self.top]

    @property
    def spatial_resolution(self) -> float:
        if self.shape[0] == 1200:
            spatial_resolution = constants.BINSIZE_1000M
        elif self.shape[0] == 2400:
            spatial_resolution = constants.BINSIZE_500M
        elif self.shape[0] == 3000:
            spatial_resolution = constants.BINSIZE_375M
        return spatial_resolution

    @property
    def wkt2(self) -> str:
        return constants.WKT2_METERS

    @property
    def epsg(self) -> None:
        return None

    @property
    def platform(self) -> str:
        product_prefix = self.product[0:3]
        return constants.PLATFORMS[product_prefix]


def viirs_metadata(
    h5_href: str, read_href_modifier: Optional[ReadHrefModifier] = None
) -> Metadata:
    xml_href = f"{h5_href}.xml"
    read_xml_href = modify_href(xml_href, read_href_modifier)

    if href_exists(read_xml_href):
        return Metadata.from_xml_and_h5(h5_href, read_href_modifier)
    else:
        return Metadata.from_h5(h5_href, read_href_modifier)
