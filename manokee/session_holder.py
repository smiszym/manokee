class SessionHolder:
    """
    Holds a reference to a session (in Application the current session)
    and notifies all observers whenever the current session changes.
    """

    def __init__(self):
        self._session = None
        self._on_session_change = None

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        if self._session is not session:
            self._session = session
            if self._on_session_change is not None:
                self._on_session_change()

    @property
    def on_session_change(self):
        return self._on_session_change

    @on_session_change.setter
    def on_session_change(self, callback):
        self._on_session_change = callback
