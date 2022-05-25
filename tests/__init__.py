from typing import Any, Dict

from stactools.testing.test_data import TestData

VNP_HAS_XML_FILE_NAMES = [
    "VNP09H1.A2012017.h00v09.001.2016294114238.h5",
    "VNP10A1.A2022097.h11v05.001.2022098094651.h5",
    "VNP13A1.A2022097.h11v05.001.2022113080900.h5",
    "VNP14A1.A2019054.h11v05.001.2019055201945.h5",
    "VNP15A2H.A2017137.h11v05.001.2018160084840.h5",
    "VNP21A1D.A2015343.h11v05.001.2019130023611.h5",
    "VNP21A1N.A2014236.h11v05.001.2019100141215.h5",
    "VNP21A2.A2021153.h11v05.001.2021237090524.h5",
    "VNP43IA4.A2012364.h11v05.001.2018186051325.h5",
]

VNP_H5_ONLY_FILE_NAMES = [
    "VNP46A2.A2022097.h11v05.001.2022105104455.h5",
]


def create_external_data_dict() -> Dict[str, Dict[str, Any]]:
    external_data: Dict[str, Dict[str, Any]] = dict()
    for file_name in VNP_HAS_XML_FILE_NAMES:
        external_data[file_name] = {
            "url": "https://ai4epublictestdata.blob.core.windows.net/stactools/viirs"
            f"/{file_name}"
        }
        external_data[f"{file_name}.xml"] = {
            "url": "https://ai4epublictestdata.blob.core.windows.net/stactools/viirs"
            f"/{file_name}.xml"
        }

    for file_name in VNP_H5_ONLY_FILE_NAMES:
        external_data[file_name] = {
            "url": "https://ai4epublictestdata.blob.core.windows.net/stactools/viirs"
            f"/{file_name}"
        }

    return external_data


external_data = create_external_data_dict()

test_data = TestData(__file__, external_data=external_data)
