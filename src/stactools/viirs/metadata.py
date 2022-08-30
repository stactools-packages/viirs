import ast
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import h5py
import rasterio
import shapely.geometry
from dateutil import parser
from stactools.core.io import ReadHrefModifier
from stactools.core.utils import href_exists
from stactools.core.utils.raster_footprint import densify_reproject_simplify

from stactools.viirs import constants, utils
from stactools.viirs.constants import VIIRSProducts

logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    """Structure to hold metadata extracted from the source H5 file.

    Although XML metadata was originally preferred since the field names are
    more consistent between products, there are several values that can only be
    obtained from the source H5 file, and the start dates in the VNP43 XML files
    are incorrect. Thus, only the H5 metadata is considered.
    """

    id: str
    product: str
    version: str
    acquisition_datetime: Optional[datetime]
    start_datetime: datetime
    end_datetime: datetime
    production_datetime: datetime
    production_julian_date: int
    horizontal_tile: int
    vertical_tile: int
    tile_id: str
    shape: List[int]
    left: float
    right: float
    top: float
    bottom: float
    xml_href: Optional[str]
    cloud_cover: Optional[int]

    @classmethod
    @utils.ignore_not_georeferenced()
    def from_h5(
        cls,
        h5_href: str,
        read_href_modifier: Optional[ReadHrefModifier] = None,
        xml_href: Optional[str] = None,
    ) -> "Metadata":
        """Extracts metadata from H5 attributes and H5 EOS metadata structure.

        Args:
            h5_href (str): HREF to the H5 source file
            read_href_modifier (ReadHrefModifier, optional): An optional
                function to modify the href (e.g. to add a token to a url)
            xml_href (str, optional): HREF to the XML metadata file

        Returns:
            Metadata: Metadata dataclass
        """
        read_h5_href = utils.modify_href(h5_href, read_href_modifier)
        with rasterio.open(read_h5_href) as dataset:
            tags = dataset.tags()
            tags = {k.lower(): v for k, v in tags.items()}

        id = utils.id_from_h5(h5_href)
        product = utils.product_from_h5(h5_href)
        version = utils.version_from_h5(h5_href)
        if version != "001":
            raise ValueError(f"Unsupported VIIRS version: {version}")

        acquisition_datetime: Optional[datetime] = None
        if product == VIIRSProducts.VNP43IA4 or product == VIIRSProducts.VNP43MA4:
            acquisition_datetime = utils.acquisition_datetime_from_h5(h5_href)
        start_datetime = parser.parse(tags["starttime"])
        end_datetime = parser.parse(tags["endtime"])
        production_datetime = parser.parse(tags["productiontime"])
        production_julian_date = utils.production_julian_date_from_h5(h5_href)

        horizontal_tile = int(tags["horizontaltilenumber"])
        vertical_tile = int(tags["verticaltilenumber"])
        tile_id = tags["tileid"]

        cloud_cover: Optional[int]
        if "hdfeos_grids_percentcloud" in tags:  # VNP09A1 and VNP09H1
            cloud_cover = round(float(tags["hdfeos_grids_percentcloud"]))
        elif "cloud_cover_extent" in tags:  # VNP10A1
            cloud_cover = round(float(str(tags["cloud_cover_extent"]).strip("%")))
        else:
            cloud_cover = None

        # rasterio does not access the EOS metadata structure
        with h5py.File(read_h5_href, "r") as h5:
            metadata_str = (
                h5["HDFEOS INFORMATION"]["StructMetadata.0"][()].decode("utf-8").strip()
            )
            metadata_split_str = [m.strip() for m in metadata_str.split("\n")]
            metadata_keys_values = [s.split("=") for s in metadata_split_str][:-1]
            metadata_dict = {key: value for key, value in metadata_keys_values}

        shape = [
            int(metadata_dict["YDim"]),
            int(metadata_dict["XDim"]),
        ]
        assert shape[0] == shape[1]

        left, top = ast.literal_eval(metadata_dict["UpperLeftPointMtrs"])
        right, bottom = ast.literal_eval(metadata_dict["LowerRightMtrs"])

        return Metadata(
            id=id,
            product=product,
            version=version,
            acquisition_datetime=acquisition_datetime,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            production_datetime=production_datetime,
            production_julian_date=production_julian_date,
            horizontal_tile=horizontal_tile,
            vertical_tile=vertical_tile,
            tile_id=tile_id,
            shape=shape,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            xml_href=xml_href,
            cloud_cover=cloud_cover,
        )

    def geometry(
        self, densification_factor: int, simplification_tolerance: float
    ) -> Dict[str, Any]:
        """GeoJSON geometry of the VIIRS tile boundary in WGS84.

        Args:
            densification_factor (int): Factor by which to increase the
                number of vertices on the image footprint. Densification
                mitigates the distortion error when reprojecting to WGS84
                geodetic coordinates.
            simplification_tolerance (float): Maximum acceptable geodetic
                distance, in degrees, between the boundary of the simplified
                footprint geometry and the original, densified geometry vertices
                after reprojection to WGS84.

        Returns:
            Dict[str, Any]: GeoJSON geometry with additional vertices.
        """
        num_rows, num_cols = self.shape
        upper_left = (0, 0)
        lower_left = (0, num_rows)
        lower_right = (num_cols, num_rows)
        upper_right = (num_cols, 0)
        pixel_points = [upper_left, lower_left, lower_right, upper_right, upper_left]

        affine = rasterio.Affine(*self.transform)
        proj_points = [affine * xy for xy in pixel_points]
        proj_polygon = shapely.geometry.polygon.Polygon(proj_points)

        wgs84_polygon: Dict[str, Any] = shapely.geometry.mapping(
            densify_reproject_simplify(
                proj_polygon,
                self.crs,
                densification_factor=densification_factor,
                precision=constants.FOOTPRINT_PRECISION,
                simplify_tolerance=simplification_tolerance,
            )
        )

        return wgs84_polygon

    @property
    def transform(self) -> List[float]:
        """Georeferencing transformation matrix for the grid data."""
        height_pixels = self.shape[0]
        width_pixels = self.shape[1]
        if self.epsg == 4326:
            # 10x10 degree geographic grid
            x_size = 10.0 / width_pixels
            y_size = 10.0 / height_pixels
            left = 10.0 * self.horizontal_tile - 180.0
            top = 90.0 - 10.0 * self.vertical_tile
        else:
            # Sinusoidal projection grid
            width_meters = self.right - self.left
            height_meters = self.top - self.bottom
            x_size = width_meters / width_pixels
            y_size = height_meters / height_pixels
            left = self.left
            top = self.top
        return [x_size, 0.0, left, 0.0, -y_size, top]

    @property
    def crs(self) -> str:
        """Grid Coordinate Reference System in EPSG or WKT2."""
        epsg = constants.EPSG.get(self.product, None)
        if epsg:
            return epsg
        else:
            return constants.SINUSOIDAL_WKT2

    @property
    def epsg(self) -> Optional[int]:
        """Grid EPSG code, if defined."""
        crs = self.crs
        if crs.startswith("PROJCS"):
            return None
        else:
            return int(crs.split(":")[-1])

    @property
    def wkt2(self) -> Optional[str]:
        """Grid WKT2, if defined."""
        crs = self.crs
        if crs.startswith("PROJCS"):
            return crs
        else:
            return None


def viirs_metadata(
    h5_href: str,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> Metadata:
    """Checks input file validity and returns a metadata class.

    Args:
        h5_href (str): HREF to the H5 data file
        read_href_modifier (ReadHrefModifier, optional): An optional function to
            modify the href (e.g. to add a token to a url)

    Returns:
        Metadata: Metadata dataclass
    """
    product = utils.product_from_h5(h5_href)
    utils.check_if_supported(product)

    xml_href: Optional[str] = f"{h5_href}.xml"
    read_xml_href = utils.modify_href(f"{h5_href}.xml", read_href_modifier)
    if not href_exists(read_xml_href):
        xml_href = None
        if product != VIIRSProducts.VNP46A2:
            logger.warning(f"Companion XML file is missing for: {h5_href}")

    return Metadata.from_h5(h5_href, read_href_modifier, xml_href)
