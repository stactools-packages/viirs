from typing import Any, Dict

from stactools.testing.test_data import TestData

VNP_PRODUCT_FILE_NAMES = {
    "VNP09H1.A2012017.h00v09.001.2016294114238.h5",
    "VNP13A1.A2022097.h11v05.001.2022113080900.h5",
}


def create_external_data_dict() -> Dict[str, Dict[str, Any]]:
    external_data: Dict[str, Dict[str, Any]] = dict()
    for file_name in VNP_PRODUCT_FILE_NAMES:
        external_data[file_name] = {
            "url": "https://ai4epublictestdata.blob.core.windows.net/stactools/viirs"
            f"/{file_name}"
        }
        external_data[f"{file_name}.xml"] = {
            "url": "https://ai4epublictestdata.blob.core.windows.net/stactools/viirs"
            f"/{file_name}.xml"
        }

    return external_data


external_data = create_external_data_dict()

test_data = TestData(__file__, external_data=external_data)
