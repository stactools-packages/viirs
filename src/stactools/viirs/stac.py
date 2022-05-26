import logging
import os
from typing import List, Optional

import pystac.utils
import stactools.core.utils.antimeridian
from pystac import Asset, Item
from pystac.extensions.projection import ProjectionExtension
from stactools.core.io import ReadHrefModifier
from stactools.core.utils.antimeridian import Strategy

from stactools.viirs import constants
from stactools.viirs.fragment import STACFragments
from stactools.viirs.metadata import viirs_metadata
from stactools.viirs.utils import add_extensions

logger = logging.getLogger(__name__)


def create_item(
    h5_href: str,
    cog_hrefs: Optional[List[str]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
    antimeridian_strategy: Strategy = Strategy.SPLIT,
) -> Item:
    """Creates a STAC Item from VIIRS data.

    Args:
        h5_href (str): href to an H5 (HDF5) file
        cog_hrefs (List[str]): List of COG asset TIF hrefs
        read_href_modifier (Callable[[str], str]): An optional function to
            modify the href (e.g. to add a token to a url)
        antimeridian_strategy (Strategy): Either split on -180 or normalize
            geometries so all longitudes are either positive or negative.

    Returns:
        pystac.Item: A STAC Item representing the VIIRS data.
    """
    metadata = viirs_metadata(h5_href, read_href_modifier)

    item = Item(
        id=metadata.id,
        geometry=metadata.geometry,
        bbox=metadata.bbox,
        datetime=None,
        properties={
            "start_datetime": pystac.utils.datetime_to_str(metadata.start_datetime),
            "end_datetime": pystac.utils.datetime_to_str(metadata.end_datetime),
            "viirs:horizontal-tile": metadata.horizontal_tile,
            "viirs:vertical-tile": metadata.vertical_tile,
            "viirs:tile-id": metadata.tile_id,
        },
    )
    item.common_metadata.created = metadata.created_datetime
    item.common_metadata.platform = metadata.platform

    stactools.core.utils.antimeridian.fix_item(item, antimeridian_strategy)

    properties = constants.HDF5_ASSET_PROPERTIES.copy()
    properties["href"] = pystac.utils.make_absolute_href(h5_href)
    item.add_asset(constants.HDF5_ASSET_KEY, Asset.from_dict(properties))

    if metadata.xml_href:
        properties = constants.METADATA_ASSET_PROPERTIES.copy()
        properties["href"] = pystac.utils.make_absolute_href(metadata.xml_href)
        item.add_asset(constants.METADATA_ASSET_KEY, Asset.from_dict(properties))

    if cog_hrefs:
        fragments = STACFragments(metadata.product)
        fragments.load_assets()
        for href in cog_hrefs:
            basename = os.path.splitext(os.path.basename(href))[0]
            subdataset_name = basename.split("_", 1)[1]
            asset_dict = fragments.subdataset_dict(subdataset_name)
            asset_dict["href"] = pystac.utils.make_absolute_href(href)
            item.add_asset(subdataset_name, Asset.from_dict(asset_dict))

    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = metadata.epsg
    projection.wkt2 = metadata.wkt2
    projection.transform = metadata.transform
    projection.shape = metadata.shape

    add_extensions(item)

    return item
