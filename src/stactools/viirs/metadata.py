import datetime
import logging
import os.path
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import fsspec
import numpy as np
import rasterio
import shapely.geometry
from dateutil import parser
from lxml import etree
from rasterio.errors import NotGeoreferencedWarning
from shapely.geometry import Polygon
from stactools.core.io import ReadHrefModifier
from stactools.core.io.xml import XmlElement
from stactools.core.projection import reproject_geom
from stactools.core.utils import href_exists

from stactools.viirs import constants, utils

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
    transform: List[float]
    xml_href: Optional[str]

    @classmethod
    def from_xml_and_h5(
        cls,
        h5_href: str,
        read_href_modifier: Optional[ReadHrefModifier] = None,
        densify_factor: Optional[int] = None,
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
        read_xml_href = utils.modify_href(xml_href, read_href_modifier)
        read_h5_href = utils.modify_href(h5_href, read_href_modifier)

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

        shape, left, top = utils.hdfeos_metadata(read_h5_href)
        transform = utils.transform(shape[0], left, top)
        geometry = cls._geometry(shape, transform, densify_factor)
        bbox = shapely.geometry.shape(geometry).bounds

        return Metadata(
            id=id,
            product=product,
            version=version,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            created_datetime=created_datetime,
            updated_datetime=updated_datetime,
            horizontal_tile=horizontal_tile,
            vertical_tile=vertical_tile,
            tile_id=tile_id,
            geometry=geometry,
            bbox=bbox,
            shape=shape,
            transform=transform,
            xml_href=xml_href,
        )

    @classmethod
    def from_h5(
        cls,
        h5_href: str,
        read_href_modifier: Optional[ReadHrefModifier] = None,
        densify_factor: Optional[int] = None,
    ) -> "Metadata":
        """Extracts metadata from H5 attributes and H5 EOS metadata structure"""
        read_h5_href = utils.modify_href(h5_href, read_href_modifier)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(read_h5_href) as dataset:
                tags = dataset.tags()
                tags = {k.lower(): v for k, v in tags.items()}

        id = os.path.splitext(tags["localgranuleid"])[0]
        product: str = tags["shortname"]
        version = tags["versionid"]

        start_datetime = parser.parse(tags["starttime"])
        end_datetime = parser.parse(tags["endtime"])
        created_datetime = parser.parse(tags["productiontime"])

        horizontal_tile = int(tags["horizontaltilenumber"])
        vertical_tile = int(tags["verticaltilenumber"])
        tile_id = tags["tileid"]

        shape, left, top = utils.hdfeos_metadata(read_h5_href)
        transform = utils.transform(shape[0], left, top)
        geometry = cls._geometry(shape, transform, densify_factor)
        bbox = shapely.geometry.shape(geometry).bounds

        return Metadata(
            id=id,
            product=product,
            version=version,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            created_datetime=created_datetime,
            updated_datetime=None,
            horizontal_tile=horizontal_tile,
            vertical_tile=vertical_tile,
            tile_id=tile_id,
            geometry=geometry,
            bbox=bbox,
            shape=shape,
            transform=transform,
            xml_href=None,
        )

    @property
    def platform(self) -> str:
        product_prefix = self.product[0:3]
        return constants.PLATFORMS[product_prefix]

    @classmethod
    def _geometry(
        cls,
        shape: List[int],
        transform: List[float],
        densify_factor: Optional[int] = None,
    ) -> Dict[str, Any]:
        num_rows, num_cols = shape
        upper_left = (0, 0)
        lower_left = (0, num_rows)
        lower_right = (num_cols, num_rows)
        upper_right = (num_cols, 0)
        pixel_points = [upper_left, lower_left, lower_right, upper_right, upper_left]

        affine = rasterio.Affine(*transform)
        proj_points = [affine * xy for xy in pixel_points]

        if densify_factor is not None:
            proj_points = cls._densify(proj_points, densify_factor)
        proj_polygon = Polygon(proj_points)
        proj_geometry = shapely.geometry.mapping(proj_polygon)
        wgs84_geometry = reproject_geom(constants.WKT2, "epsg:4326", proj_geometry)

        return wgs84_geometry

    @classmethod
    def _densify(
        cls, point_list: List[Tuple[float, float]], densify_factor: int
    ) -> List[Tuple[float, float]]:
        # https://stackoverflow.com/questions/64995977/generating-equidistance-points-along-the-boundary-of-a-polygon-but-cw-ccw  # noqa
        points: Any = np.asarray(point_list)
        densified_number = len(points) * densify_factor
        existing_indices = np.arange(0, densified_number, densify_factor)
        interp_indices = np.arange(existing_indices[-1])
        interp_x = np.interp(interp_indices, existing_indices, points[:, 0])
        interp_y = np.interp(interp_indices, existing_indices, points[:, 1])
        densified_points = [(x, y) for x, y in zip(interp_x, interp_y)]
        return densified_points


def viirs_metadata(
    h5_href: str,
    read_href_modifier: Optional[ReadHrefModifier] = None,
    densify_factor: Optional[int] = None,
) -> Metadata:
    """Creates a metadata class from the appropriate source (XML or H5).

    Metadata based on XML data is preferred (over the H5 data file) since it is
    consistent between products; the same can not be said of the H5 attributes.

    Args:
        h5_href (str): HREF to the H5 data file
        read_href_modifier (Optional[ReadHrefModifier], optional): An optional
            function to modify the HREF (e.g. to add a token to a url)

    Returns:
        Metadata: Metadata class
    """
    xml_href = f"{h5_href}.xml"
    read_xml_href = utils.modify_href(xml_href, read_href_modifier)

    if href_exists(read_xml_href):
        return Metadata.from_xml_and_h5(h5_href, read_href_modifier, densify_factor)
    else:
        return Metadata.from_h5(h5_href, read_href_modifier, densify_factor)
