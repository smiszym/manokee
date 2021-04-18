from typing import Optional

import pygit2


class SessionHistory:
    def __init__(self, session_path: Optional[str]):
        self.session_path = session_path
        self.repo = None
        self.status = None
        self.log = None
        if self.session_path is not None:
            try:
                self.repo = pygit2.Repository(self.session_path)
            except pygit2.GitError:
                pass

    def exists(self):
        return self.repo is not None

    def init(self):
        if self.exists():
            return
        self.repo = pygit2.init_repository(self.session_path)
        self.refresh()

    def refresh(self):
        # Checking repository state is too expensive to do it in regular intervals.

        # TODO: Don't read the whole log each time refresh() is called, but rather
        # try to incrementally check if there are new commits compared to those we know

        if not self.repo:
            self.status = None
            self.log = None
            return

        self.status = self.repo.status()
        self.log = [
            (commit.commit_time, commit.message)
            for commit in self.repo.walk(self.repo.head.target)
        ]

    def to_js(self):
        return {
            "status": self.status,
            "log": self.log,
        }
