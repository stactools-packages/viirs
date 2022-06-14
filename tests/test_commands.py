import glob
import os
from tempfile import TemporaryDirectory
from typing import Callable, List

import pystac
from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.viirs.commands import create_viirs_command
from tests import test_data


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_viirs_command]

    def test_create_cogs(self) -> None:
        filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
        infile = test_data.get_external_data(filename)
        with TemporaryDirectory() as tmp_dir:
            cmd = f"viirs create-cogs {infile} -o {tmp_dir}"
            self.run_command(cmd)
            tif_files = glob.glob(f"{tmp_dir}/*.tif")
            self.assertEqual(len(tif_files), 5)

    def test_create_item(self) -> None:
        filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
        infile = test_data.get_external_data(filename)
        with TemporaryDirectory() as tmp_dir:
            cmd = f"viirs create-item {infile} {tmp_dir} -c"
            self.run_command(cmd)
            item_path = os.path.join(tmp_dir, f"{os.path.splitext(filename)[0]}.json")
            item = pystac.read_file(item_path)
        item.validate()

    def test_create_collection(self) -> None:
        filename = "VNP09H1.A2012017.h00v09.001.2016294114238.h5"
        product = filename.split(".")[0]
        infile = test_data.get_external_data(filename)
        with TemporaryDirectory() as tmp_dir:
            text_filename = f"{tmp_dir}/list.txt"
            with open(text_filename, "w") as txt_file:
                txt_file.write(infile)
            cmd = f"viirs create-collection {text_filename} {tmp_dir}"
            self.run_command(cmd)
            collection_path = os.path.join(tmp_dir, f"{product}/collection.json")
            collection = pystac.read_file(collection_path)
            collection.validate()
