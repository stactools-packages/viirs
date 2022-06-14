# stactools-viirs

[![PyPI](https://img.shields.io/pypi/v/stactools-viirs)](https://pypi.org/project/stactools-viirs/)

- Name: viirs
- Package: `stactools.viirs`
- PyPI: https://pypi.org/project/stactools-viirs/
- Owner: @pjhartzell
- Dataset homepage: https://viirsland.gsfc.nasa.gov/index.html
- STAC extensions used:
  - [classification](https://github.com/stac-extensions/classification/)
  - [eo](https://github.com/stac-extensions/eo)
  - [item-assets](https://github.com/stac-extensions/item-assets)
  - [proj](https://github.com/stac-extensions/projection)
  - [raster](https://github.com/stac-extensions/raster)
  - [scientific](https://github.com/stac-extensions/scientific)
- Extra fields:
  - `viirs:horizontal-tile`
  - `viirs:vertical-tile`
  - `viirs:tile-id`

Use this repository to create STAC Items and Collections for [VIIRS](https://viirsland.gsfc.nasa.gov/index.html) data.

## STAC Examples

There is an example Collection and Item for each VIIRS product supported by this repository in the [examples](examples) directory.

## Installation
```shell
pip install stactools-viirs
```

## Command-line Usage

VIIRS products are delivered as an H5 (HDF5) file with a corresponding XML metadata file. This stactools package uses information from both files for STAC creation and expects them to exist in the same directory. The Black Marble (VNP46A2) product is an exception since it is not delivered with an XML metadata file.

To create a STAC Item from a single VIIRS H5 file (and corresponding XML file):

```shell
$ stac viirs create-item <H5 file path> <output directory>
```

To create COGs for each subdataset in the H5 file and include them as Assets in the STAC Item, append the `-c` flag to the command.

To create a STAC Collection, enter H5 file paths into a text file with one file path per line. Then pass the text file to the `create-collection` command:

```shell
$ stac viirs create-collection <text file path> <output directory>
```

If the text file contains H5 file paths from multiple VIIRS products, multiple STAC Collections will be created. If COGs exist alongside the H5 files, they will be included as Assets in the STAC Items contained in the Collection(s).

Use `stac viirs --help` to see all subcommands and options.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
$ pip install -e .
$ pip install -r requirements-dev.txt
$ pre-commit install
```

To check all files:

```shell
$ pre-commit run --all-files
```

To run the tests:

```shell
$ pytest -vv
```
