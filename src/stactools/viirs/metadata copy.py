import datetime
import os.path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import fsspec
import shapely.geometry
from lxml import etree
from shapely.geometry import Polygon
from stactools.core.io import ReadHrefModifier
from stactools.core.io.xml import XmlElement

from stactools.viirs import utils


class MissingElement(Exception):
    """An expected element is missing from the XML file"""


@dataclass(frozen=True)
class Metadata:
    """Structure to hold values fetched from a metadata XML file or other metadata source."""

    id: str
    product: str
    version: str
    geometry: Optional[Dict[str, Any]]
    bbox: Optional[List[float]]
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    created: Optional[datetime.datetime]
    updated: Optional[datetime.datetime]
    horizontal_tile: int
    vertical_tile: int
    tile_id: str

    @classmethod
    def from_hdf5_href(
        cls, hdf5_href: str, read_href_modifier: Optional[ReadHrefModifier] = None
    ) -> "Metadata":
        """Reads metadat from an XML href.

        Args:
            href (str): The href of the xml metadata file
            read_href_modifier (Optional[Callable[[str], str]]): Optional
                function to modify the read href

        Returns:
            Metadata: Information that will map to Item attributes.
        """
        self.xml_href = f"{hdf5_href}.xml"

        def missing_element(attribute: str) -> Callable[[str], Exception]:
            def get_exception(xpath: str) -> Exception:
                return MissingElement(
                    f"Could not find attribute `{attribute}` at xpath '{xpath}' at href {href}"
                )

            return get_exception

        if read_href_modifier:
            read_href = read_href_modifier(href)
        else:
            read_href = href
        with fsspec.open(read_href) as file:
            root = XmlElement(etree.parse(file, base_url=href).getroot())

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
        version = utils.version_string(
            metadata.find_text_or_throw(
                "CollectionMetaData/VersionID", missing_element("version")
            )
        )

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

        created = datetime.datetime.fromisoformat(
            metadata.find_text_or_throw(
                "ECSDataGranule/ProductionDateTime", missing_element("created")
            )
        )
        updated = datetime.datetime.fromisoformat(
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

        return Metadata(
            id=id,
            product=product,
            version=version,
            geometry=geometry,
            bbox=bbox,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            created=created,
            updated=updated,
            horizontal_tile=horizontal_tile,
            vertical_tile=vertical_tile,
            tile_id=tile_id,
        )

    @classmethod
    def from_h5_href(
        cls, href: str, read_href_modifier: Optional[ReadHrefModifier] = None
    ) -> None:
        """Reads metadat from an H5 href.

        Args:
            href (str): The href of the h5 file
            read_href_modifier (Optional[Callable[[str], str]]): Optional
                function to modify the read href

        Returns:
            Metadata: Information that will map to Item attributes.
        """
        # This will be needed for VNP10A1 and VNP46A2, which do not have 
        # sidecar xml metadata files

    @property
    def collection(self) -> str:
        return self.product[3:]

    def projection(self):
        subdatasets = stactools.viirs.utils.subdatasets(file.hdf_href)
        if not subdatasets:
            raise ValueError(
                f"No subdatasets found in HDF file: {file.hdf_href}")
        with rasterio.open(subdatasets[0]) as dataset:
            crs = dataset.crs
            proj_bbox = dataset.bounds
            proj_transform = list(dataset.transform)[0:6]
            proj_shape = dataset.shape
        proj_geometry = shapely.geometry.mapping(
            shapely.geometry.box(*proj_bbox))
        projection = ProjectionExtension.ext(item, add_if_missing=True)
        projection.epsg = None
        projection.wkt2 = crs.to_wkt("WKT2")
        projection.geometry = proj_geometry
        projection.transform = proj_transform
        projection.shape = proj_shape