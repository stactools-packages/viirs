import glob
import os

from stactools.viirs import stac

EXAMPLE_H5_FILES = [
    "VNP09H1.A2012017.h00v09.001.2016294114238.h5",
    "VNP10A1.A2022097.h11v05.001.2022098094651.h5",
    "VNP13A1.A2022097.h11v05.001.2022113080900.h5",
    "VNP14A1.A2019054.h11v05.001.2019055201945.h5",
    "VNP15A2H.A2017137.h11v05.001.2018160084840.h5",
    "VNP21A1D.A2015343.h11v05.001.2019130023611.h5",
    "VNP21A1N.A2014236.h11v05.001.2019100141215.h5",
    "VNP21A2.A2021153.h11v05.001.2021237090524.h5",
    "VNP43IA4.A2012364.h11v05.001.2018186051325.h5",
    "VNP46A2.A2022097.h11v05.001.2022105104455.h5",
]


for href in EXAMPLE_H5_FILES:
    product = href.split(".")[0]
    path = "tests/data-files/external"
    cog_hrefs = glob.glob(f"{path}/{product}*.tif")
    if cog_hrefs:
        item = stac.create_item(f"tests/data-files/external/{href}", cog_hrefs=cog_hrefs)
    else:
        item = stac.create_item(f"tests/data-files/external/{href}")
    item_path = os.path.join(f"examples/{product}", f"{item.id}.json")
    item.set_self_href(item_path)
    item.make_asset_hrefs_relative()
    item.validate()
    item.save_object()
