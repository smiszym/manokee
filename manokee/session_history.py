from typing import Optional

import pygit2


class SessionHistory:
    def __init__(self, session_path: Optional[str]):
        self.session_path = session_path
        self.repo = None
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

    def status(self):
        return self.repo.status() if self.repo else None

    def log(self):
        return (
            [
                (commit.commit_time, commit.message)
                for commit in self.repo.walk(self.repo.head.target)
            ]
            if self.repo
            else None
        )

    def to_js(self):
        return {
            "status": self.status(),
            "log": self.log(),
        }
