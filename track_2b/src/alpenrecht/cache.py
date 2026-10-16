"""cache/ only lives while a question is being answered.

Parallel steps of one question (and parallel questions) share downloaded law texts, crawls and extracted texts through
cache/. When the last running request finishes, every file in it is deleted except the user's uploads, which later
questions of the chat still refer to. KEEP_CACHE=1 turns this off.
"""
import threading
from contextlib import contextmanager

from . import config
from . import sources

_active = 0
_guard = threading.Lock()


def clear():
    """Delete the cached files (directories stay: the modules write into them without re-creating them)."""
    for path in config.CACHE_DIR.rglob("*"):
        if path.is_file() and "uploads" not in path.relative_to(config.CACHE_DIR).parts:
            try:
                path.unlink()
            except OSError:  # still open by a straggling worker thread: the next clear gets it
                pass
    with sources._LOCKS_GUARD:
        sources._LOCKS.clear()


@contextmanager
def in_use():
    global _active
    with _guard:
        _active += 1
    try:
        yield
    finally:
        with _guard:
            _active -= 1
            if _active == 0 and not config.KEEP_CACHE:
                clear()


def stream(events):
    """Wrap an event generator: the cache is held until it is exhausted or closed (client gone)."""
    with in_use():
        yield from events
