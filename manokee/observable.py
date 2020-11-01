from typing import Set
from weakref import WeakMethod


class ObservableMixin:
    def __init__(self):
        self._observers: Set[WeakMethod] = set()

    def add_observer(self, callback):
        self._observers.add(WeakMethod(callback))

    def _notify_observers(self):
        for ref in self._observers:
            callback = ref()
            if callback:
                callback()
