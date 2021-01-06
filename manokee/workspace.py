import os
import os.path


def dir_is_session(path):
    """
    Checks whether a given directory contains Manokee session.
    :param path: Path to a directory.
    :return: True if this directory contains Manokee session.
    """
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "session.mnk"))


class Workspace:
    def __init__(self, directory=None):
        self._directory = directory
        self._sessions = []
        self.refresh()

    @property
    def sessions(self):
        return self._sessions

    def refresh(self):
        """
        Refresh the list of sessions contained in the workspace, by reading
        the workspace directory contents from the filesystem.
        """
        if self._directory is None:
            self._sessions = []
            return
        else:
            self._sessions = sorted(
                [path for path in _abslistdir(self._directory) if dir_is_session(path)]
            )

    def session_file_path_for_session_name(self, name):
        # Verify that name is a filename without path separators
        assert "\0" not in name and "/" not in name
        return os.path.join(self._directory, name, "session.mnk")


def _abslistdir(path):
    return (os.path.join(path, file) for file in os.listdir(path))
