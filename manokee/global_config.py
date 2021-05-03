import os
import re


def read_global_config():
    result = {}
    path = os.path.join(os.environ["HOME"], ".manokeerc")
    with open(path) as f:
        for line in f:
            match = re.match("([a-zA-Z0-9_]*)=(.*)$", line)
            if match is not None:
                key = match.group(1)
                value = match.group(2)
                result[key] = value
            else:
                raise ValueError(f"Cannot parse config line `{line.rstrip()}`")
    return result
