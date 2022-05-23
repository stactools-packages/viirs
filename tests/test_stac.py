import pytest
import shapely.geometry
from stactools.core.utils.antimeridian import Strategy

from stactools.viirs import stac
from tests import VNP_PRODUCT_FILE_NAMES, test_data

# class StacTest(unittest.TestCase):
#     def test_create_collection(self) -> None:
#         # Write tests for each for the creation of a STAC Collection
#         # Create the STAC Collection...
#         collection = stac.create_collection()
#         collection.set_self_href("")

#         # Check that it has some required attributes
#         self.assertEqual(collection.id, "my-collection-id")
#         # self.assertEqual(collection.other_attr...

#         # Validate
#         collection.validate()

#     def test_create_item(self) -> None:
#         href = test_data.get_external_data()
#         item = stac.create_item(
#             "zz-mystuff/VNP09H1/11/05/2022097/VNP09H1.A2022097.h11v05.001.2022105085030.h5"
#         )

#         # self.assertEqual(item.id, "VNP13A1.A2022097.h11v05.001.2022113080900")

#         item.validate()


def test_read_href_modifier() -> None:
    href = test_data.get_external_data("VNP09H1.A2012017.h00v09.001.2016294114238.h5")

    did_it = False

    def read_href_modifier(href: str) -> str:
        nonlocal did_it
        did_it = True
        return href

    _ = stac.create_item(href, read_href_modifier=read_href_modifier)
    assert did_it


def test_antimeridian() -> None:
    href = test_data.get_external_data("VNP09H1.A2012017.h00v09.001.2016294114238.h5")
    item = stac.create_item(href, antimeridian_strategy=Strategy.NORMALIZE)
    bounds = shapely.geometry.shape(item.geometry).bounds
    assert bounds[0] == -180.07153
    assert bounds[2] == -169.92014
    item.validate()


@pytest.mark.parametrize("file_name", VNP_PRODUCT_FILE_NAMES)
def test_vnp_h5_and_xml_assets(file_name: str) -> None:
    infile = test_data.get_external_data(file_name)
    _ = test_data.get_external_data(f"{file_name}.xml")
    item = stac.create_item(infile)
    item.validate()
    assert "hdf5" in item.assets
    assert "metadata" in item.assets
