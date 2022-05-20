import datetime
import os.path
from typing import Callable, Optional

import fsspec
import shapely.geometry
from lxml import etree
from shapely.geometry import Polygon
from stactools.core.io import ReadHrefModifier
from stactools.core.io.xml import XmlElement
import rasterio
from stactools.core.utils import href_exists

from stactools.viirs import utils


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
        self.xml_href = f"{h5_href}.xml"
        
        if read_href_modifier:
            self.read_h5_href = read_href_modifier(h5_href)
            self.read_xml_href = read_href_modifier(self.xml_href)
        else:
            self.read_h5_href = self.h5_href
            self.read_xml_href = self.xml_href

        subdatasets = utils.subdatasets(self.read_h5_href)
        if not subdatasets:
            raise ValueError(
                f"No subdatasets found in H5 file: {h5_href}")
        with rasterio.open(subdatasets[0]) as dataset:
            crs = dataset.crs
            print(crs)
            self.transform = list(dataset.transform)[0:6]
            print(self.transform)
            self.shape = dataset.shape
            print(self.shape)
        self.epsg = None
        self.wkt2 = crs.to_wkt("WKT2")

        # future: check if an h5 only dataset
        self._xml_metadata

    @property
    def xml_href(self) -> Optional[str]:
        xml_href = f"{self.h5_href}.xml"
        if href_exists(xml_href):
            return xml_href
        else:
            return None

    def _xml_metadata(self):

        def missing_element(attribute: str) -> Callable[[str], Exception]:
            def get_exception(xpath: str) -> Exception:
                return MissingElement(
                    f"Could not find attribute `{attribute}` at xpath '{xpath}' at href {href}"
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
        self.version = utils.version_string(
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
        self.geometry = shapely.geometry.mapping(polygon)
        self.bbox = polygon.bounds

        start_date = metadata.find_text_or_throw(
            "RangeDateTime/RangeBeginningDate", missing_element("start_date")
        )
        start_time = metadata.find_text_or_throw(
            "RangeDateTime/RangeBeginningTime", missing_element("start_time")
        )
        self.start_datetime = datetime.datetime.fromisoformat(f"{start_date}T{start_time}")
        end_date = metadata.find_text_or_throw(
            "RangeDateTime/RangeEndingDate", missing_element("end_date")
        )
        end_time = metadata.find_text_or_throw(
            "RangeDateTime/RangeEndingTime", missing_element("end_time")
        )
        self.end_datetime = datetime.datetime.fromisoformat(f"{end_date}T{end_time}")

        self.created = datetime.datetime.fromisoformat(
            metadata.find_text_or_throw(
                "ECSDataGranule/ProductionDateTime", missing_element("created")
            )
        )
        self.updated = datetime.datetime.fromisoformat(
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

    def _h5_meta(self):
        # This will be needed for VNP46A2, which does not have sidecar xml
        # metadata files
        pass

    @property
    def collection(self) -> str:
        return self.product[3:]
