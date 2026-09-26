# 2026-09-26: both portals collapsed onto one URL each (/diwan/requests,
# /diwan/queue), with the former per-page routes now just ?tab= values on
# that one page - see those two index.py files. The nav_panel() macro in
# diwan_shell.html already renders whatever's in this list generically
# (comparing item.route == active_route for the is-active highlight), so
# this is the only place that needed to change to make the existing rail/
# side-nav point at tabs instead of separate pages - the shell itself
# needed no changes.
REQUESTER_PORTAL_NAV = [
	{"route": "/diwan/requests?tab=submit", "label": "New Request", "icon": "send"},
	{"route": "/diwan/requests", "label": "My Requests", "icon": "list"},
]

DIWAN_PORTAL_NAV = [
	{"route": "/diwan/queue", "label": "Queue", "icon": "inbox"},
	{"route": "/diwan/queue?tab=tray", "label": "Bulk Approve", "icon": "tray"},
	{"route": "/diwan/queue?tab=delivery_sheets", "label": "Delivery Sheets", "icon": "printer"},
	{"route": "/diwan/queue?tab=envelopes", "label": "Envelopes", "icon": "printer"},
	{"route": "/diwan/queue?tab=audit_log", "label": "Access Log", "icon": "shield"},
]
