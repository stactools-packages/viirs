from asyncio import constants
from curses import meta
import logging
from datetime import datetime, timezone
from typing import Optional, List

import pystac.utils
from pystac import (
    CatalogType,
    Collection,
    Extent,
    Item,
    Provider,
    ProviderRole,
    SpatialExtent,
    TemporalExtent,
    Asset,
)

from pystac.extensions.projection import ProjectionExtension
from stactools.core.io import ReadHrefModifier
from stactools.core.utils.antimeridian import Strategy
import stactools.core.utils.antimeridian

from stactools.viirs.metadata import Metadata
from stactools.viirs import constants

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
        antimeridian_strategy (AntimeridianStrategy): Either split on -180 or
            normalize geometries so all longitudes are either positive or negative.

    Returns:
        pystac.Item: A STAC Item representing the VIIRS data.
    """
    metadata = Metadata(h5_href, read_href_modifier)

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
    stactools.core.utils.antimeridian.fix_item(item, antimeridian_strategy)

    item.common_metadata.created = metadata.created_datetime

    properties = constants.HDF5_ASSET_PROPERTIES.copy()
    properties["href"] = h5_href
    item.add_asset(constants.HDF5_ASSET_KEY, Asset.from_dict(properties))

    # properties = METADATA_ASSET_PROPERTIES.copy()
    # properties["href"] = xml_href
    # item.add_asset(METADATA_ASSET_KEY, Asset.from_dict(properties))

    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = metadata.epsg
    projection.wkt2 = metadata.wkt2
    projection.geometry = metadata.geometry
    projection.transform = metadata.transform
    projection.shape = metadata.shape

    return item


def create_collection() -> Collection:
    """Create a STAC Collection

    This function includes logic to extract all relevant metadata from
    an asset describing the STAC collection and/or metadata coded into an
    accompanying constants.py file.

    See `Collection<https://pystac.readthedocs.io/en/latest/api.html#collection>`_.

    Returns:
        Collection: STAC Collection object
    """
    providers = [
        Provider(
            name="The OS Community",
            roles=[ProviderRole.PRODUCER, ProviderRole.PROCESSOR, ProviderRole.HOST],
            url="https://github.com/stac-utils/stactools",
        )
    ]

    # Time must be in UTC
    demo_time = datetime.now(tz=timezone.utc)

    extent = Extent(
        SpatialExtent([[-180.0, 90.0, 180.0, -90.0]]),
        TemporalExtent([[demo_time, None]]),
    )

    collection = Collection(
        id="my-collection-id",
        title="A dummy STAC Collection",
        description="Used for demonstration purposes",
        license="CC-0",
        providers=providers,
        extent=extent,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    return collection
