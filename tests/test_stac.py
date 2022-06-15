import os

import pytest
import shapely.geometry
from stactools.core.utils.antimeridian import Strategy

from stactools.viirs import stac
from tests import VNP_H5_ONLY_FILE_NAMES, VNP_HAS_XML_FILE_NAMES, test_data


def test_read_href_modifier() -> None:
    filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
    href = test_data.get_external_data(filename)
    _ = test_data.get_external_data(f"{filename}.xml")

    did_it = False

    def read_href_modifier(href: str) -> str:
        nonlocal did_it
        did_it = True
        return href

    _ = stac.create_item(href, read_href_modifier=read_href_modifier)
    assert did_it


def test_antimeridian_normalize() -> None:
    filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
    href = test_data.get_external_data(filename)
    _ = test_data.get_external_data(f"{filename}.xml")
    item = stac.create_item(href, antimeridian_strategy=Strategy.NORMALIZE)
    bounds = shapely.geometry.shape(item.geometry).bounds
    assert bounds[0] == pytest.approx(-182.7767901225167)
    assert bounds[2] == pytest.approx(-169.99999998473047)
    item.validate()


def test_antimeridian_split() -> None:
    filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
    href = test_data.get_external_data(filename)
    _ = test_data.get_external_data(f"{filename}.xml")
    item = stac.create_item(href, antimeridian_strategy=Strategy.SPLIT)
    item_dict = item.to_dict()
    assert len(item_dict["geometry"]["coordinates"]) == 2
    item.validate()


@pytest.mark.parametrize("file_name", VNP_HAS_XML_FILE_NAMES)
def test_h5_and_xml_exist(file_name: str) -> None:
    href = test_data.get_external_data(file_name)
    _ = test_data.get_external_data(f"{file_name}.xml")
    item = stac.create_item(href)
    assert "hdf5" in item.assets
    assert "metadata" in item.assets
    item.validate()


@pytest.mark.parametrize("file_name", VNP_H5_ONLY_FILE_NAMES)
def test_only_h5_exists(file_name: str) -> None:
    href = test_data.get_external_data(file_name)
    item = stac.create_item(href)
    assert "hdf5" in item.assets
    assert "metadata" not in item.assets
    item.validate()


def test_asset_updates() -> None:
    filename = "VNP09A1.A2012017.h00v09.001.2016294114238.h5"
    basename = os.path.splitext(filename)[0]
    cog_name = [f"{basename}_SurfReflect_M1.tif"]
    href = test_data.get_external_data(filename)
    _ = test_data.get_external_data(f"{filename}.xml")
    item = stac.create_item(href, cog_hrefs=cog_name)
    assets = {k: v.to_dict() for k, v in item.assets.items()}
    raster_bands = assets["SurfReflect_M1"]["raster:bands"][0]
    assert raster_bands["nodata"] == 0

    filename = "VNP09A1.A2022145.h11v05.001.2022154194417.h5"
    basename = os.path.splitext(filename)[0]
    cog_name = [f"{basename}_SurfReflect_M1.tif"]
    href = test_data.get_external_data(filename)
    _ = test_data.get_external_data(f"{filename}.xml")
    item = stac.create_item(href, cog_hrefs=cog_name)
    assets = {k: v.to_dict() for k, v in item.assets.items()}
    raster_bands = assets["SurfReflect_M1"]["raster:bands"][0]
    assert raster_bands["nodata"] == -28672


def test_densify() -> None:
    filename = "VNP13A1.A2022097.h11v05.001.2022113080900.h5"
    href = test_data.get_external_data(filename)
    _ = test_data.get_external_data(f"{filename}.xml")

    item = stac.create_item(href)
    item_dict = item.to_dict()
    assert len(item_dict["geometry"]["coordinates"][0]) == 5
    item.validate()

    item = stac.create_item(href, densify_factor=2)
    item_dict = item.to_dict()
    assert len(item_dict["geometry"]["coordinates"][0]) == 9
    item.validate()
