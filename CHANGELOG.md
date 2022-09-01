# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project attempts to match the major and minor versions of [stactools](https://github.com/stac-utils/stactools) and increments the patch number as needed.

## [Unreleased]

### Added

- Added an `eo:bands` list to appropriate Collection summaries. ([#13](https://github.com/stactools-packages/viirs/pull/13))
- Added an option to create Item geometry from the valid (not nodata) raster data area. ([#14](https://github.com/stactools-packages/viirs/pull/14))
- Added Python 3.10 support. ([#14](https://github.com/stactools-packages/viirs/pull/14))

### Changed

- Collection extents are now updated from the Collection Items when creating a collection with the CLI ([#13](https://github.com/stactools-packages/viirs/pull/13))

### Removed

- Dropped Python 3.7 support. ([#14](https://github.com/stactools-packages/viirs/pull/14))

## [0.1.0] - 2022-06-22

Initial release.

[Unreleased]: <https://github.com/stactools-packages/viirs/compare/v0.1.0..main/>
[0.1.0]: <https://github.com/stactools-packages/viirs/releases/tag/v0.1.0>
