# stactools-viirs

[![PyPI](https://img.shields.io/pypi/v/stactools-viirs)](https://pypi.org/project/stactools-viirs/)

- Name: viirs
- Package: `stactools.viirs`
- PyPI: https://pypi.org/project/stactools-viirs/
- Owner: @githubusername
- Dataset homepage: http://example.com
- STAC extensions used:
  - [proj](https://github.com/stac-extensions/projection/)
- Extra fields:
  - `viirs:custom`: A custom attribute

A short description of the package and its usage.

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item/item.json)

## Installation
```shell
pip install stactools-viirs
```

## Command-line Usage

Description of the command line functions

```shell
$ stac viirs create-item source destination
```

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
