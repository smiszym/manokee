import gc
from manokee.observable import ObservableMixin
import manokee.session


class SessionHolder(ObservableMixin):
    """
    Holds a reference to a session (in Application the current session)
    and notifies all observers whenever the current session changes.
    """

    def __init__(self):
        super().__init__()
        self._session = None

    @property
    def session(self) -> "manokee.session.Session":
        return self._session

    @session.setter
    def session(self, session: "manokee.session.Session"):
        if self._session is not session:
            self._session = session
            self._notify_observers()
            # Sessions are huge objects, typically a few hundred MB.
            # Run the garbage collector after loading new sessions,
            # in order to free the memory as soon as possible.
            gc.collect()
