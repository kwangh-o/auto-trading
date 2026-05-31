import threading

from models.state import AppState
from services.state_store import StateStore

_lock = threading.RLock()
_state_store = StateStore()
_app_state: AppState = _state_store.load()


class _StateManager:
    @property
    def lock(self) -> threading.RLock:
        return _lock

    @property
    def app_state(self) -> AppState:
        return _app_state

    def save(self) -> None:
        _state_store.save(_app_state)


state_manager = _StateManager()
