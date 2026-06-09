"""<<< --------------------------------------------------- IMPORTS --------------------------------------------------- >>>"""

import json
import os
import random
import subprocess
import threading
import time

from libqtile import bar, hook, layout, widget
from libqtile.config import Click, Drag, DropDown, Group, Key, Match, ScratchPad, Screen

try:
    from libqtile.lazy import lazy
except ImportError:
    from libqtile.command import lazy


try:
    from libqtile import qtile as global_qtile
except ImportError:
    global_qtile = None

"""<<< ----------------------------------------------- HYPERPARAMETERS ----------------------------------------------- >>>"""

mod = "mod4"
fn = "mod1"
hash_sym = chr(35)

terminal = "alacritty"
browser = "zen-browser"
file_manager = "nemo"
screenshot_tool = "spectacle"
power_menu = "eww"
application_launcher = "rofi"
system_monitor = "btop"

"""<<< ---------------------------------------------------- PYWAL ---------------------------------------------------- >>>"""

WAL_FILE = os.path.expanduser("~/.cache/wal/colors.json")


def _load_wal():
    """Load pywal colors from cache. Returns (colors_dict, special_dict)."""
    if os.path.exists(WAL_FILE):
        try:
            with open(WAL_FILE) as f:
                wal = json.load(f)
            return wal.get("colors", {}), wal.get("special", {})
        except json.JSONDecodeError, KeyError, OSError:
            pass
    return {}, {}


def _build_palette(colors, special):
    """Turn raw wal dicts into named aliases used by the bar."""
    bg = special.get("background", colors.get("color0", "#1a1a2e"))
    fg = special.get("foreground", colors.get("color7", "#abb2bf"))
    accent = colors.get("color4", "#61afef")
    muted = colors.get("color8", "#3e4452")
    good = colors.get("color2", "#98c379")
    warn = colors.get("color3", "#e5c07b")
    alert = colors.get("color1", "#e06c75")
    purple = colors.get("color5", "#c678dd")

    return dict(
        bg=bg,
        fg=fg,
        accent=accent,
        muted=muted,
        good=good,
        warn=warn,
        alert=alert,
        purple=purple,
    )


_raw_colors, _raw_special = _load_wal()
PALETTE = _build_palette(_raw_colors, _raw_special)

# ── Live color-reload ──────────────────────────────────────────────────────────
_LIVE_WIDGETS: dict = {}


def reload_wal_colors(qtile_obj=None):
    """Re-read ~/.cache/wal/colors.json and push new colors live (Crash-Safe)."""
    raw_c, raw_s = _load_wal()
    p = _build_palette(raw_c, raw_s)
    PALETTE.update(p)

    mapping = {
        "arch_logo": [("foreground", p["accent"])],
        "groupbox": [
            ("active", p["fg"]),
            ("inactive", p["muted"]),
            ("this_current_screen_border", p["accent"]),
            ("other_current_screen_border", p["purple"]),
            ("this_screen_border", p["muted"]),
            ("urgent_border", p["alert"]),
        ],
        "windowname": [("foreground", p["muted"])],
        "clock_time": [("foreground", p["accent"])],
        "clock_sep": [("foreground", p["muted"])],
        "clock_date": [("foreground", p["muted"])],
        "cpu_icon": [("foreground", p["warn"])],
        "cpu": [("foreground", p["warn"])],
        "mem_icon": [("foreground", p["purple"])],
        "mem": [("foreground", p["purple"])],
        "vol_icon": [("foreground", p["fg"])],
        "vol": [("foreground", p["fg"])],
        "wifi_icon": [("foreground", p["good"])],
        "bat": [("foreground", p["good"]), ("low_foreground", p["alert"])],
        "sep_title": [("foreground", p["muted"])],
        "sep_notif": [("foreground", p["muted"])],
        "sep_res": [("foreground", p["muted"])],
        "sep_vol": [("foreground", p["muted"])],
        "sep_wifi": [("foreground", p["muted"])],
        "sep_bat": [("foreground", p["muted"])],
        "current_layout": [("foreground", p["accent"])],
        "sep_layout": [("foreground", p["muted"])],
        "notif_icon": [("foreground", p["muted"])],
    }

    for key, attrs in mapping.items():
        w = _LIVE_WIDGETS.get(key)
        if w is None:
            continue
        for attr, value in attrs:
            try:
                setattr(w, attr, value)
            except AttributeError, Exception:
                pass
        try:
            w.draw()
        except Exception:
            pass

    instance = qtile_obj or global_qtile

    if instance:
        try:
            for group in instance.groups:
                for lay in group.layouts:
                    if hasattr(lay, "border_focus"):
                        lay.border_focus = p["accent"]
                    if hasattr(lay, "border_normal"):
                        lay.border_normal = p["muted"]

                for win in group.windows:
                    if win.floating and hasattr(win, "paint_borders"):
                        win.paint_borders(p["accent"] if win.has_focus else p["muted"])

            for screen in instance.screens:
                if screen.top and hasattr(screen.top, "draw"):
                    screen.top.draw()

            if hasattr(instance, "current_screen") and instance.current_screen:
                if instance.current_window:
                    instance.current_screen.group.focus(instance.current_window)
        except Exception:
            pass


# ── Automatischer Watcher ─────────────────────────────────────────────────────
def _start_wal_watcher():
    """Startet einen Background-Thread, der colors.json auf Änderungen überwacht."""

    def _watcher():
        last_mtime = 0.0
        while True:
            try:
                mtime = os.path.getmtime(WAL_FILE)
                if mtime != last_mtime:
                    last_mtime = mtime
                    time.sleep(0.3)
                    reload_wal_colors()
            except OSError:
                pass
            time.sleep(1.2)

    t = threading.Thread(target=_watcher, daemon=True)
    t.start()


"""<<< -------------------------------------------------- FUNCTIONS -------------------------------------------------- >>>"""


def _trigger_postscripts():
    """Führt die Reload-Scripte sicher aus, z.B. für Alacritty (Inode Fix) und GTK."""
    scripts = [
        os.path.expanduser("~/.config/wal/postscripts/alacritty_reload.sh"),
        os.path.expanduser("~/.config/wal/postscripts/rofi_reload.sh"),
        os.path.expanduser("~/.config/wal/postscripts/gtk_wal_reload.sh"),
        os.path.expanduser("~/.config/wal/postscripts/cursor_reload.sh"),
        os.path.expanduser("~/.config/wal/postscripts/starship_reload.sh"),
    ]
    for script in scripts:
        if os.path.exists(script):
            subprocess.run([script], capture_output=True)


def change_wallpaper(qtile_obj=None):
    """Pick a random wallpaper, run pywal quietly, then trigger postscripts."""
    wall_dir = os.path.expanduser("~/.wallpapers")
    os.makedirs(wall_dir, exist_ok=True)
    files = [
        f for f in os.listdir(wall_dir) if f.lower().endswith((".jpg", ".png", ".jpeg"))
    ]
    if not files:
        return
    full_path = os.path.join(wall_dir, random.choice(files))

    # Wal im quiet-Modus ausführen, damit es uns nicht das Terminal vollspammt
    subprocess.run(["wal", "-q", "-i", full_path])

    # Der Alacritty / Inode Fix
    _trigger_postscripts()


def safe_restart(qtile_obj=None):
    """Cross-Version sicherer Neustart."""
    instance = qtile_obj or global_qtile
    if instance:
        try:
            instance.reload_config()
        except AttributeError:
            try:
                instance.restart()
            except AttributeError:
                pass


"""<<< ------------------------------------------------- KEYBINDINGS ------------------------------------------------- >>>"""

keys = [
    Key([mod], "Return", lazy.spawn(terminal), desc="Terminal"),
    Key([mod], "BackSpace", lazy.spawn(browser), desc="Browser"),
    Key([mod], "b", lazy.spawn(system_monitor), desc="btop"),
    Key([mod], "f", lazy.spawn(file_manager), desc="Files"),
    Key([mod, fn], "p", lazy.spawn(power_menu), desc="Power menu"),
    Key([fn], "p", lazy.spawn(screenshot_tool), desc="Screenshot"),
    Key(
        [mod],
        "space",
        lazy.spawn(application_launcher + " -show drun"),
        desc="Launcher",
    ),
    Key(
        [mod],
        "g",
        lazy.spawn(f"{browser} -new-tab https://gemini.google.com/app"),
        desc="Gemini",
    ),
    # Media & System Controls (Neu hinzugefügt)
    Key(
        [],
        "XF86AudioRaiseVolume",
        lazy.spawn("pactl set-sink-volume @DEFAULT_SINK@ +5%"),
        desc="Volume Up",
    ),
    Key(
        [],
        "XF86AudioLowerVolume",
        lazy.spawn("pactl set-sink-volume @DEFAULT_SINK@ -5%"),
        desc="Volume Down",
    ),
    Key(
        [],
        "XF86AudioMute",
        lazy.spawn("pactl set-sink-mute @DEFAULT_SINK@ toggle"),
        desc="Volume Mute",
    ),
    Key([], "XF86AudioPlay", lazy.spawn("playerctl play-pause"), desc="Play/Pause"),
    Key([], "XF86AudioNext", lazy.spawn("playerctl next"), desc="Next Track"),
    Key([], "XF86AudioPrev", lazy.spawn("playerctl previous"), desc="Prev Track"),
    Key(
        [],
        "XF86MonBrightnessUp",
        lazy.spawn("brightnessctl set +5%"),
        desc="Brightness Up",
    ),
    Key(
        [],
        "XF86MonBrightnessDown",
        lazy.spawn("brightnessctl set 5%-"),
        desc="Brightness Down",
    ),
    # Window Management
    Key([mod], "Right", lazy.screen.next_group()),
    Key([mod], "Left", lazy.screen.prev_group()),
    Key([fn], "f", lazy.window.toggle_floating()),
    Key([mod], "n", lazy.layout.maximize()),
    Key([mod], "m", lazy.window.minimize()),
    Key([mod], "k", lazy.window.kill()),
    Key([mod], "a", lazy.layout.left()),
    Key([mod], "d", lazy.layout.right()),
    Key([mod], "s", lazy.layout.down()),
    Key([mod], "w", lazy.layout.up()),
    Key([mod, "shift"], "a", lazy.layout.grow_left()),
    Key([mod, "shift"], "d", lazy.layout.grow_right()),
    Key([mod, "shift"], "s", lazy.layout.grow_down()),
    Key([mod, "shift"], "w", lazy.layout.grow_up()),
    Key([mod, "shift"], "q", lazy.shutdown()),
    Key([mod, "shift"], "x", lazy.shutdown()),
    Key([mod, "shift"], "r", lazy.function(safe_restart)),
    Key([mod], "F12", lazy.group["scratchpad"].dropdown_toggle("term")),
    Key([fn], "w", lazy.function(change_wallpaper)),
    Key(
        [fn, "shift"],
        "r",
        lazy.function(reload_wal_colors),
        desc="Reload wal colors live",
    ),
]

"""<<< ------------------------------------------------- WORKSPACES -------------------------------------------------- >>>"""

groups = [Group(str(i)) for i in range(1, 8)]

for i in groups:
    keys.extend(
        [
            Key([mod], i.name, lazy.group[i.name].toscreen()),
            Key([mod, "shift"], i.name, lazy.window.togroup(i.name)),
        ]
    )

"""<<< --------------------------------------------------- LAYOUTS --------------------------------------------------- >>>"""

layouts = [
    layout.MonadTall(
        border_focus=PALETTE["accent"],
        border_normal=PALETTE["muted"],
        border_width=3,
        margin=8,
    ),
    layout.Max(),
]

"""<<< ------------------------------------------------- AUTO START -------------------------------------------------- >>>"""

subprocess.Popen(["/home/tobster/.config/qtile/autostart.sh"])


@hook.subscribe.startup_once
def auto_start():
    wall_dir = os.path.expanduser("~/.wallpapers")
    if os.path.isdir(wall_dir):
        files = [
            f
            for f in os.listdir(wall_dir)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ]
        if files:
            random_wall = os.path.join(wall_dir, random.choice(files))
            subprocess.run(["wal", "-q", "-i", random_wall])
            _trigger_postscripts()

    subprocess.Popen(["picom", "-b"])
    subprocess.Popen(["setxkbmap", "de"])
    subprocess.Popen(["eww", "daemon"])
    subprocess.Popen(
        ["xrandr", "--output", "eDP-1", "--mode", "1920x1080", "--pos", "0x0"]
    )
    subprocess.Popen(["xsetroot", "-cursor_name", "left_ptr"])

    _start_wal_watcher()


"""<<< ---------------------------------------------------- BAR ------------------------------------------------------ >>>"""

FONT = "JetBrainsMono Nerd Font"
FSIZE = 14


def _make_bar_bg(alpha_hex: str = "CC") -> str:
    bg = "000000"
    return f"#{bg}{alpha_hex}"


# Hier ist die Transparenz! CC -> 80%. B3 -> 70% (etwas transparenter).
BAR_BG = _make_bar_bg("B3")


def _gap(n=8):
    return widget.Spacer(length=n)


def _pipe(key):
    # Dünnerer, eleganterer Trennstrich statt dem fetten "|"
    w = widget.TextBox(
        text="│", font=FONT, fontsize=FSIZE, foreground=PALETTE["muted"], padding=6
    )
    _LIVE_WIDGETS[key] = w
    return w


def _icon(key, text, color_key):
    w = widget.TextBox(
        text=text, font=FONT, fontsize=FSIZE, foreground=PALETTE[color_key], padding=4
    )
    _LIVE_WIDGETS[key] = w
    return w


def set_bar():
    p = PALETTE

    arch_logo = widget.TextBox(
        text="󰣇",
        font=FONT,
        fontsize=18,
        foreground=p["accent"],
        padding=8,
        mouse_callbacks={"Button1": lambda: None},
    )
    _LIVE_WIDGETS["arch_logo"] = arch_logo

    gbox = widget.GroupBox(
        font=FONT,
        fontsize=FSIZE,
        padding=6,
        borderwidth=2,
        highlight_method="line",
        this_current_screen_border=p["accent"],
        other_current_screen_border=p["purple"],
        this_screen_border=p["muted"],
        other_screen_border=p["muted"],
        highlight_color=["#00000000", "#00000000"],
        active=p["fg"],
        inactive=p["muted"],
        urgent_border=p["alert"],
        background=None,
        disable_drag=True,
        rounded=False,
        use_mouse_wheel=False,
    )
    _LIVE_WIDGETS["groupbox"] = gbox

    wname = widget.WindowName(
        font=FONT,
        fontsize=FSIZE,
        foreground=p["muted"],
        max_chars=40,
        empty_group_string="",
    )
    _LIVE_WIDGETS["windowname"] = wname

    clk_time = widget.Clock(
        format="%H:%M",
        font=FONT,
        fontsize=16,
        foreground=p["accent"],
        padding=0,
    )
    _LIVE_WIDGETS["clock_time"] = clk_time

    clk_sep = widget.TextBox(
        text="  ",
        font=FONT,
        fontsize=FSIZE,
        foreground=p["muted"],
        padding=0,
    )
    _LIVE_WIDGETS["clock_sep"] = clk_sep

    clk_date = widget.Clock(
        format="%a %d.%m.%Y",
        font=FONT,
        fontsize=FSIZE,
        foreground=p["muted"],
        padding=0,
    )
    _LIVE_WIDGETS["clock_date"] = clk_date

    # --- Fancy & Reliable System Widgets ---

    cpu = widget.CPU(
        font=FONT,
        fontsize=FSIZE,
        foreground=p["warn"],
        format="{load_percent:02.0f}%",  # Feste Breite gegen Jitter
        update_interval=2,
        padding=0,
    )
    _LIVE_WIDGETS["cpu"] = cpu

    mem = widget.Memory(
        font=FONT,
        fontsize=FSIZE,
        foreground=p["purple"],
        format="{MemPercent:02.0f}%",  # Feste Breite gegen Jitter
        update_interval=2,
        padding=0,
    )
    _LIVE_WIDGETS["mem"] = mem

    try:
        # PulseVolume ist auf modernen Pipewire-Systemen viel verlässlicher!
        vol = widget.PulseVolume(
            font=FONT,
            fontsize=FSIZE,
            foreground=p["fg"],
            padding=0,
            update_interval=0.1,
            limit_max_volume=True,
        )
    except Exception:
        vol = widget.TextBox(
            text="vol?", font=FONT, fontsize=FSIZE, foreground=p["muted"], padding=0
        )
    _LIVE_WIDGETS["vol"] = vol

    try:
        bat = widget.Battery(
            font=FONT,
            fontsize=FSIZE,
            format="{char} {percent:2.0%}",
            charge_char="󰂄",
            discharge_char="󰁹",
            full_char="󰁹",
            empty_char="󰂎",
            unknown_char="󰂑",
            low_percentage=0.2,
            low_foreground=p["alert"],
            foreground=p["good"],
            notify_below=20,
            padding=0,
            update_interval=5,
        )
    except Exception:
        bat = widget.TextBox(
            text="", font=FONT, fontsize=FSIZE, foreground=p["muted"], padding=0
        )
    _LIVE_WIDGETS["bat"] = bat

    curr_layout = widget.CurrentLayout(
        font=FONT, fontsize=FSIZE, foreground=p["accent"], padding=4
    )
    _LIVE_WIDGETS["current_layout"] = curr_layout

    # Fancy Icons
    cpu_icon = _icon("cpu_icon", " ", "warn")
    mem_icon = _icon("mem_icon", " ", "purple")
    vol_icon = _icon("vol_icon", " ", "fg")
    wifi_icon = _icon("wifi_icon", "󰤨 ", "good")

    blocks = (
        [
            _gap(4),
            arch_logo,
            _pipe("sep_arch"),
            gbox,
            _gap(6),
            _pipe("sep_title"),
            _gap(6),
            wname,
        ]
        + [widget.Spacer(), clk_time, clk_sep, clk_date, widget.Spacer()]
        + [
            cpu_icon,
            cpu,
            _gap(4),
            mem_icon,
            mem,
            _pipe("sep_res"),
            vol_icon,
            vol,
            _pipe("sep_vol"),
            wifi_icon,
            bat,  # Hat jetzt sein eigenes Lade-Icon integriert!
            _pipe("sep_bat"),
            curr_layout,
            _pipe("sep_layout"),
            widget.Systray(padding=8, icon_size=18),
            _gap(10),
        ]
    )

    return [
        Screen(
            top=bar.Bar(
                blocks,
                32,
                background=BAR_BG,
                margin=[6, 10, 0, 10],
                border_width=0,
                opacity=1.0,
            ),
        )
    ]


screens = set_bar()

"""<<< ---------------------------------------------------- MOUSE ---------------------------------------------------- >>>"""

mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()
    ),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

"""<<< ------------------------------------------------- SCRATCHPAD -------------------------------------------------- >>>"""

groups.append(
    ScratchPad(
        "scratchpad",
        [
            DropDown(
                "term", terminal, width=0.6, height=0.6, x=0.2, y=0.1, opacity=0.9
            ),
        ],
    )
)

"""<<< ---------------------------------------------------- MAIN ----------------------------------------------------- >>>"""

dgroups_app_rules = []
dgroups_key_binder = None
dgroups_focus_by_rule = False
dgroups_match_by_rule = True
dgroups_repeat_once = True

follow_mouse_focus = True
bring_front_on_focus = False
cursor_warp = False

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirm"),
        Match(wm_class="dialog"),
        Match(wm_class="download"),
        Match(wm_class="error"),
        Match(wm_class="file_progress"),
        Match(wm_class="notification"),
        Match(wm_class="splash"),
        Match(wm_class="toolbar"),
        Match(wm_class="ssh-askpass"),
        Match(wm_class="pinentry"),
        Match(wm_class="confirmreset"),
        Match(title="makebranch"),
        Match(title="maketag"),
        Match(title="branchdialog"),
        Match(title="pinentry"),
    ],
    border_focus=PALETTE["accent"],
    border_normal=PALETTE["muted"],
    border_width=3,
)

auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
auto_minimize = True

wmname = "LG3D"
