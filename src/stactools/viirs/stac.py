import logging
import os
from typing import List, Optional

import pystac.utils
import stactools.core.utils.antimeridian
from pystac import Asset, Collection, Item, Summaries
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.scientific import ScientificExtension
from stactools.core.io import ReadHrefModifier
from stactools.core.utils.antimeridian import Strategy

from stactools.viirs import constants
from stactools.viirs.fragment import STACFragments
from stactools.viirs.metadata import viirs_metadata
from stactools.viirs.utils import find_extensions

logger = logging.getLogger(__name__)


def create_item(
    h5_href: str,
    cog_hrefs: Optional[List[str]] = None,
    read_href_modifier: Optional[ReadHrefModifier] = None,
    antimeridian_strategy: Strategy = Strategy.SPLIT,
    densify_factor: Optional[int] = None,
) -> Item:
    """Creates a STAC Item from VIIRS data.

    Args:
        h5_href (str): href to an H5 (HDF5) file
        cog_hrefs (List[str], optional): Optional list of COG asset TIF hrefs
        read_href_modifier (Callable[[str], str], optional): An optional
            function to modify the href (e.g. to add a token to a url)
        antimeridian_strategy (Strategy, optional): Either split on -180 or
            normalize geometries so all longitudes are either positive or
            negative. Default is to split antimeridian geometries.
        densify_factor (int, optional): Factor by which to increase the number
            of vertices on the geometry to mitigate projection error.

    Returns:
        pystac.Item: A STAC Item representing the VIIRS data.
    """
    metadata = viirs_metadata(h5_href, read_href_modifier, densify_factor)

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
    item.common_metadata.platform = constants.PLATFORM
    item.common_metadata.instruments = constants.INSTRUMENT

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
        for href in cog_hrefs:
            basename = os.path.splitext(os.path.basename(href))[0]
            subdataset_name = basename.split("_", 1)[1]
            asset_dict = fragments.subdataset_dict(subdataset_name)
            asset_dict["href"] = pystac.utils.make_absolute_href(href)
            item.add_asset(subdataset_name, Asset.from_dict(asset_dict))

    projection = ProjectionExtension.ext(item, add_if_missing=True)
    projection.epsg = metadata.epsg
    if projection.epsg is None:
        projection.wkt2 = metadata.wkt2
    projection.transform = metadata.transform
    projection.shape = metadata.shape

    assets_dict = {k: v.to_dict() for k, v in item.assets.items()}
    extensions = find_extensions(assets_dict)
    item.stac_extensions.extend(extensions)
    item.stac_extensions = list(set(item.stac_extensions))
    item.stac_extensions.sort()

    return item


def create_collection(product: str) -> Collection:
    """Creates a STAC Collection for a VIIRS product.

    Args:
        product (str): VIIRS product, e.g., 'VNP13A1'

    Returns:
        Collection: A STAC Collection for the product.
    """
    summaries = {
        "instruments": constants.INSTRUMENT,
        "platform": [constants.PLATFORM],
    }

    fragments = STACFragments(product)
    collection_fragments = fragments.collection_dict()
    collection = Collection(
        id=collection_fragments["id"],
        title=collection_fragments["title"],
        description=collection_fragments["description"],
        license=collection_fragments["license"],
        keywords=collection_fragments["keywords"],
        providers=collection_fragments["providers"],
        extent=collection_fragments["extent"],
        summaries=Summaries(summaries),
    )
    collection.add_links(collection_fragments["links"])

    item_assets_dict = {
        constants.HDF5_ASSET_KEY: constants.HDF5_ASSET_PROPERTIES,
        constants.METADATA_ASSET_KEY: constants.METADATA_ASSET_PROPERTIES,
    }
    item_assets_dict.update(fragments.assets_dict())
    item_assets = {k: AssetDefinition(v) for k, v in item_assets_dict.items()}
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_ext.item_assets = item_assets

    ScientificExtension.add_to(collection)
    collection.extra_fields["sci:doi"] = collection_fragments["sci:doi"]

    extensions = find_extensions(item_assets_dict)
    collection.stac_extensions.extend(extensions)
    collection.stac_extensions = list(set(collection.stac_extensions))
    collection.stac_extensions.sort()

    return collection
