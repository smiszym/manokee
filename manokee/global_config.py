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


class RecentSessions:
    def __init__(self):
        self._list = []

    def read(self):
        # TODO: Change the format to an SQLite database with metadata like
        # last access date, etc.
        self._list = []
        path = os.path.join(os.environ["HOME"], ".manokee-sessions")
        try:
            with open(path) as f:
                for line in f:
                    self._list.append(line.rstrip())
        except FileNotFoundError:
            pass

    def write(self):
        path = os.path.join(os.environ["HOME"], ".manokee-sessions")
        with open(path, "w") as f:
            for session in self._list:
                f.write(session)
                f.write("\n")

    def get(self):
        return self._list

    def append(self, session):
        if session not in self._list:
            self._list.append(session)
