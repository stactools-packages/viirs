import json
import unittest

from stactools.viirs import stac


class StacTest(unittest.TestCase):
    def test_create_collection(self) -> None:
        # Write tests for each for the creation of a STAC Collection
        # Create the STAC Collection...
        collection = stac.create_collection()
        collection.set_self_href("")

        # Check that it has some required attributes
        self.assertEqual(collection.id, "my-collection-id")
        # self.assertEqual(collection.other_attr...

        # Validate
        collection.validate()

    def test_create_item(self) -> None:
        item = stac.create_item(
            "zz-mystuff/VNP13A1/20220407/VNP13A1.A2022097.h11v05.001.2022113080900.h5.xml"
        )

        # self.assertEqual(item.id, "VNP13A1.A2022097.h11v05.001.2022113080900")

        item.validate()

        print(json.dumps(item.to_dict(), indent=4))
