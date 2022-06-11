import stactools.core
from stactools.cli.registry import Registry

from stactools.viirs.stac import create_collection, create_item

__all__ = ["create_item", "create_collection"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.viirs import commands

    registry.register_subcommand(commands.create_viirs_command)


__version__ = "0.1.0"
