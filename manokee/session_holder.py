from manokee.session import Session


class SessionHolder:
    """
    Holds a reference to a session (in Application the current session)
    and notifies all observers whenever the current session changes.
    """

    def __init__(self):
        self._session = None
        self.on_session_change = None

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session):
        if self._session is not session:
            self._session = session
            if self.on_session_change is not None:
                self.on_session_change()
