import os
import time
import threading
from dotenv import dotenv_values

try:
    from libqtile import qtile as global_qtile
except ImportError:
    global_qtile = None

ENV_FILE = "/home/tobster/os/qtile/env/system_colors.env"
LIVE_WIDGETS = {}

def _load_env_colors():
    if not os.path.exists(ENV_FILE):
        return {}
    return dotenv_values(ENV_FILE)

def reload_wal_colors(qtile_obj=None):
    p = _load_env_colors()
    if not p:
        return

    mapping = {
        "arch_logo": [("foreground", p.get("LOGO_COLOR"))],
        "groupbox": [
            ("active", p.get("TEXT_FG")),
            ("inactive", p.get("TEXT_MUTED")),
            ("this_current_screen_border", p.get("ACCENT_ACTIVE")),
            ("other_current_screen_border", p.get("ACCENT_INACTIVE")),
            ("this_screen_border", p.get("TEXT_MUTED")),
            ("urgent_border", p.get("CPU_RAM_COLOR")),
        ],
        "windowname": [("foreground", p.get("TEXT_MUTED"))],
        "clock_time": [("foreground", p.get("CLOCK_COLOR"))],
        "clock_sep": [("foreground", p.get("SEP_COLOR"))],
        "clock_date": [("foreground", p.get("TEXT_MUTED"))],
        "cpu_icon": [("foreground", p.get("CPU_RAM_COLOR"))],
        "cpu": [("foreground", p.get("CPU_RAM_COLOR"))],
        "mem_icon": [("foreground", p.get("CPU_RAM_COLOR"))],
        "mem": [("foreground", p.get("CPU_RAM_COLOR"))],
        "vol_icon": [("foreground", p.get("AUDIO_COLOR"))],
        "vol": [("foreground", p.get("AUDIO_COLOR"))],
        "sep_title": [("foreground", p.get("SEP_COLOR"))],
        "sep_notif": [("foreground", p.get("SEP_COLOR"))],
        "sep_res": [("foreground", p.get("SEP_COLOR"))],
        "sep_vol": [("foreground", p.get("SEP_COLOR"))],
        "current_layout": [("foreground", p.get("LAYOUT_COLOR"))],
        "sep_layout": [("foreground", p.get("SEP_COLOR"))],
        "notif_icon": [("foreground", p.get("TEXT_MUTED"))],
    }

    for key, attrs in mapping.items():
        w = LIVE_WIDGETS.get(key)
        if w is None:
            continue
        for attr, value in attrs:
            try:
                setattr(w, attr, value)
            except Exception:
                pass
        try:
            w.draw()
        except Exception:
            pass

    instance = qtile_obj or global_qtile
    if instance:
        try:
            accent = p.get("ACCENT_ACTIVE")
            muted = p.get("TEXT_MUTED")

            for group in instance.groups:
                for lay in group.layouts:
                    if hasattr(lay, "border_focus"):
                        lay.border_focus = accent
                    if hasattr(lay, "border_normal"):
                        lay.border_normal = muted

                # FEHLER BEHOBEN: Diese Schleife muss EINGERÜCKT sein,
                # damit sie für JEDE Gruppe ausgeführt wird.
                for win in group.windows:
                    if win.floating and hasattr(win, "paint_borders"):
                        win.paint_borders(accent if win.has_focus else muted)

            for screen in instance.screens:
                if screen.top and hasattr(screen.top, "draw"):
                    screen.top.draw()

            if hasattr(instance, "current_screen") and instance.current_screen:
                if instance.current_window:
                    instance.current_screen.group.focus(instance.current_window)
        except Exception as e:
            pass

def start_env_watcher(qtile_obj=None):
    def _watcher():
        last_mtime = 0.0
        while True:
            try:
                mtime = os.path.getmtime(ENV_FILE)
                if mtime != last_mtime:
                    last_mtime = mtime
                    time.sleep(0.3)

                    # FEHLER BEHOBEN: Sicheres Ausführen im Qtile Main-Thread
                    instance = qtile_obj or global_qtile
                    if instance and hasattr(instance, "call_soon_threadsafe"):
                        instance.call_soon_threadsafe(reload_wal_colors, instance)
                    else:
                        reload_wal_colors(instance)

            except OSError:
                pass
            time.sleep(1.2)

    t = threading.Thread(target=_watcher, daemon=True)
    t.start()
