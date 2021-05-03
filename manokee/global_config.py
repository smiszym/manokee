import os

import toml


def read_global_config():
    try:
        return toml.load(
            os.path.join(os.environ["HOME"], ".config", "manokee", "config.toml")
        )
    except FileNotFoundError:
        return {}
