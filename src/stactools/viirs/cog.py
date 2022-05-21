import os
from typing import List, Tuple

import stactools.core.utils.convert


def cogify(infile: str, outdir: str) -> Tuple[List[str], List[str]]:
    """Creates cogs for the provided H5 file.

    Args:
        infile (str): The input H5 file
        outdir (str): The output directory

    Returns:
        Tuple[List[str], List[str]]: A two tuple (paths, names):
            - The first element is a list of the output tif paths
            - The second element is a list of subdataset names
    """
    subdatasets = stactools.viirs.utils.subdatasets(infile)
    base_file_name = os.path.splitext(os.path.basename(infile))[0]
    paths = []
    subdataset_names = []
    for subdataset in subdatasets:
        parts1 = subdataset.split(":")
        subdataset_path = parts1[-1]
        parts2 = subdataset_path.split("/")
        subdataset_name = parts2[-1]
        sanitized_subdataset_name = subdataset_name.replace(" ", "_")
        subdataset_names.append(sanitized_subdataset_name)
        file_name = f"{base_file_name}_{sanitized_subdataset_name}.tif"
        outfile = os.path.join(outdir, file_name)
        stactools.core.utils.convert.cogify(subdataset, outfile)
        paths.append(outfile)
    return (paths, subdataset_names)

    # need to add transform and crs to a profile dict
