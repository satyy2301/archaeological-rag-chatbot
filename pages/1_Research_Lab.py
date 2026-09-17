"""Research Lab workbench — main tool orchestration page."""

from ui.components import dispatch_active_station, render_lab_topbar
from ui.preload import ensure_lab_warmed
from ui.session import initialize_session_state
from ui.sidebar import render_sidebar
from ui.theme import inject_theme

initialize_session_state()
ensure_lab_warmed(async_load=False)
inject_theme("lab")
render_lab_topbar()
render_sidebar()
dispatch_active_station()
