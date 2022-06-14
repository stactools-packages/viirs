import os.path
from tempfile import TemporaryDirectory
from unittest import TestCase

import rasterio

import stactools.viirs.cog
from stactools.viirs.stac import create_item
from tests import test_data

SUBDATASET_NAMES = [
    "SurfReflect_I1",
    "SurfReflect_I2",
    "SurfReflect_I3",
    "SurfReflect_QC_500m",
    "SurfReflect_State_500m",
]

COG_LIST = [
    f"VNP09H1.A2012017.h00v09.001.2016294114238_{subdataset_name}.tif"
    for subdataset_name in SUBDATASET_NAMES
]


class CogTest(TestCase):
    def test_item_with_cogs(self) -> None:
        filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
        href = test_data.get_external_data(filename)
        _ = test_data.get_external_data(f"{filename}.xml")
        item = create_item(href, cog_hrefs=COG_LIST)
        assert all(f"{subdataset}" in item.assets for subdataset in SUBDATASET_NAMES)
        assert "hdf5" in item.assets
        assert "metadata" in item.assets
        self.assertEqual(len(item.assets), len(SUBDATASET_NAMES) + 2)
        item.validate()

    def test_item_without_cogs(self) -> None:
        filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
        href = test_data.get_external_data(filename)
        _ = test_data.get_external_data(f"{filename}.xml")
        item = create_item(href)
        assert "hdf5" in item.assets
        assert "metadata" in item.assets
        self.assertEqual(len(item.assets), 2)
        item.validate()

    def test_create_cogs(self) -> None:
        filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
        href = test_data.get_external_data(filename)
        _ = test_data.get_external_data(f"{filename}.xml")
        with TemporaryDirectory() as tmp_dir:
            paths = stactools.viirs.cog.cogify(href, tmp_dir)
            assert all(os.path.exists(path) for path in paths)
        self.assertEqual(len(paths), 5)
        file_names = [os.path.basename(path) for path in paths]
        expected_cog_names = COG_LIST
        self.assertEqual(set(file_names), set(expected_cog_names))

    def test_int8toint16_nodata(self) -> None:
        filename = "VNP13A1.A2022097.h11v05.001.2022113080900.h5"
        href = test_data.get_external_data(filename)
        _ = test_data.get_external_data(f"{filename}.xml")
        with TemporaryDirectory() as tmp_dir:
            paths = stactools.viirs.cog.cogify(href, tmp_dir)
            native_int8_cog = next(
                (path for path in paths if "pixel_reliability.tif" in path)
            )
            with rasterio.open(native_int8_cog, "r") as src:
                assert src.dtypes[0] == "int16"
                assert src.nodata == -32768
