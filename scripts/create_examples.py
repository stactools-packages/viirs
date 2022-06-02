import os
import sys

from stactools.viirs import cog, stac

EXAMPLE_H5_FILES = [
    "VNP09H1.A2012017.h00v09.001.2016294114238.h5",
    "VNP10A1.A2022097.h11v05.001.2022098094651.h5",
    "VNP13A1.A2022097.h11v05.001.2022113080900.h5",
    "VNP14A1.A2019054.h11v05.001.2019055201945.h5",
    "VNP15A2H.A2017137.h11v05.001.2018160084840.h5",
    # "VNP21A1D.A2015343.h11v05.001.2019130023611.h5",
    # "VNP21A1N.A2014236.h11v05.001.2019100141215.h5",
    # "VNP21A2.A2021153.h11v05.001.2021237090524.h5",
    # "VNP43IA4.A2012364.h11v05.001.2018186051325.h5",
    # "VNP46A2.A2022097.h11v05.001.2022105104455.h5",
]


def examples(create_cogs: bool) -> None:
    h5_dir_path = "tests/data-files/external"
    for href in EXAMPLE_H5_FILES:
        product = href.split(".")[0]
        h5_file_path = f"{h5_dir_path}/{href}"
        if create_cogs:
            cog_hrefs = cog.cogify(h5_file_path, h5_dir_path)
            item = stac.create_item(h5_file_path, cog_hrefs=cog_hrefs)
        else:
            item = stac.create_item(h5_file_path)
        item_path = os.path.join(f"examples/{product}", f"{item.id}.json")
        item.set_self_href(item_path)
        item.make_asset_hrefs_relative()
        item.validate()
        item.save_object(include_self_link=False)


if __name__ == "__main__":
    create_cogs = sys.argv[1]
    if len(sys.argv) == 1:
        examples(False)
    elif sys.argv[1] == "-c":
        examples(True)
    else:
        print("Only valid option is `-c` for creating COGs")
