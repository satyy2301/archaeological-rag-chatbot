"""Background warming of heavy lab modules for faster page transitions."""

import logging
import threading

logger = logging.getLogger(__name__)

_warm_lock = threading.Lock()
_warmed = False
_warm_started = False


def _warm_imports() -> None:
    """Import lab modules so subsequent navigation reuses cached modules."""
    global _warmed
    with _warm_lock:
        if _warmed:
            return
        import lab.services  # noqa: F401
        import ui.stations  # noqa: F401
        _warmed = True
        logger.info("Lab modules warmed")


def ensure_lab_warmed(async_load: bool = True) -> None:
    """Warm lab imports on landing (async) or block until ready on lab page."""
    global _warm_started
    if _warmed:
        return
    if async_load:
        with _warm_lock:
            if _warm_started:
                return
            _warm_started = True
        threading.Thread(target=_warm_imports, daemon=True).start()
    else:
        _warm_imports()
