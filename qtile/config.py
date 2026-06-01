"""<<< --------------------------------------------------- IMPORTS --------------------------------------------------- >>>"""

import os
import json
import random
import subprocess
from libqtile import layout, widget, bar, hook, qtile as _qtile_instance
from libqtile.config import Group, Key, Screen, ScratchPad, DropDown, Match, Drag, Click
try:
    from libqtile.lazy import lazy
except ImportError:
    from libqtile.command import lazy

"""<<< ----------------------------------------------- HYPERPARAMETERS ----------------------------------------------- >>>"""

mod  = "mod4"
fn   = "mod1"
hash_sym = chr(35)

terminal             = "alacritty"
browser              = "zen-browser"
file_manager         = "thunar"
screenshot_tool      = "spectacle"
power_menu           = "eww"
application_launcher = "rofi"

"""<<< ---------------------------------------------------- PYWAL ---------------------------------------------------- >>>"""

WAL_FILE = os.path.expanduser("~/.cache/wal/colors.json")

def _load_wal():
    """Load pywal colors from cache. Returns (colors_dict, special_dict)."""
    if os.path.exists(WAL_FILE):
        try:
            with open(WAL_FILE) as f:
                wal = json.load(f)
            return wal.get("colors", {}), wal.get("special", {})
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    return {}, {}

def _build_palette(colors, special):
    """Turn raw wal dicts into named aliases used by the bar."""
    bg     = special.get("background", colors.get("color0",  "#1a1a2e"))
    fg     = special.get("foreground", colors.get("color7",  "#abb2bf"))
    accent = colors.get("color4",  "#61afef")   # blue  — active group / clock
    muted  = colors.get("color8",  "#3e4452")   # gray  — separators / inactive
    good   = colors.get("color2",  "#98c379")   # green — battery / wifi
    warn   = colors.get("color3",  "#e5c07b")   # amber — cpu / mem
    alert  = colors.get("color1",  "#e06c75")   # red   — low battery / urgent
    purple = colors.get("color5",  "#c678dd")   # purple— layout / ram
    return dict(bg=bg, fg=fg, accent=accent, muted=muted,
                good=good, warn=warn, alert=alert, purple=purple)

_raw_colors, _raw_special = _load_wal()
PALETTE = _build_palette(_raw_colors, _raw_special)

# ── Live color-reload ──────────────────────────────────────────────────────────
_LIVE_WIDGETS: dict = {}

def reload_wal_colors(qtile=None):
    """Re-read ~/.cache/wal/colors.json and push new colors to every bar widget."""
    raw_c, raw_s = _load_wal()
    p = _build_palette(raw_c, raw_s)
    PALETTE.update(p)

    mapping = {
        "groupbox":          [("active",      p["fg"]),
                              ("inactive",    p["muted"]),
                              ("this_current_screen_border", p["accent"]),
                              ("other_current_screen_border", p["purple"]),
                              ("this_screen_border", p["muted"]),
                              ("urgent_border", p["alert"])],
        "windowname":        [("foreground",  p["muted"])],
        "clock_time":        [("foreground",  p["accent"])],
        "clock_sep":         [("foreground",  p["muted"])],
        "clock_date":        [("foreground",  p["muted"])],
        "cpu_icon":          [("foreground",  p["warn"])],
        "cpu":               [("foreground",  p["warn"])],
        "mem_icon":          [("foreground",  p["purple"])],
        "mem":               [("foreground",  p["purple"])],
        "vol_icon":          [("foreground",  p["fg"])],
        "vol":               [("foreground",  p["fg"])],
        "wifi_icon":         [("foreground",  p["good"])],
        "wifi":              [("foreground",  p["good"])],
        "bat":               [("foreground",  p["good"]),
                              ("low_foreground", p["alert"])],
        "sep_notif":         [("foreground",  p["muted"])],
        "sep_res":           [("foreground",  p["muted"])],
        "sep_vol":           [("foreground",  p["muted"])],
        "sep_wifi":          [("foreground",  p["muted"])],
        "sep_bat":           [("foreground",  p["muted"])],
        "sep_layout":        [("foreground",  p["muted"])],
        "notif_icon":        [("foreground",  p["muted"])],
    }

    for key, attrs in mapping.items():
        w = _LIVE_WIDGETS.get(key)
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

    # Layout borders live updaten
    try:
        instance = qtile or _qtile_instance
        for group in instance.groups:
            for lay in group.layouts:
                if hasattr(lay, 'border_focus'):
                    lay.border_focus = p["accent"]
                if hasattr(lay, 'border_normal'):
                    lay.border_normal = p["muted"]
    except Exception:
        pass

    # Bar background
    try:
        bg_with_alpha = p["bg"] + "E6"
        for screen in (qtile or _qtile_instance).screens:
            if screen.top:
                screen.top.background = bg_with_alpha
                screen.top.draw()
    except Exception:
        pass

"""<<< -------------------------------------------------- FUNCTIONS -------------------------------------------------- >>>"""

def change_wallpaper(qtile=None):
    """Pick a random wallpaper, run pywal. The postscript handles color reload."""
    wall_dir = os.path.expanduser("~/.wallpapers")
    os.makedirs(wall_dir, exist_ok=True)
    files = [f for f in os.listdir(wall_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if not files:
        return
    full_path = os.path.join(wall_dir, random.choice(files))
    subprocess.Popen(["wal", "-i", full_path])

def safe_restart(qtile):
    try:
        qtile.reload_config()
    except AttributeError:
        qtile.restart()

"""<<< ------------------------------------------------- KEYBINDINGS ------------------------------------------------- >>>"""

keys = [
    Key([mod], "Return",        lazy.spawn(terminal),                              desc="Terminal"),
    Key([mod], "BackSpace",     lazy.spawn(browser),                               desc="Browser"),
    Key([mod], "f",             lazy.spawn(file_manager),                          desc="Files"),
    Key([mod, fn], "p",         lazy.spawn(power_menu),                            desc="Power menu"),
    Key([fn], "p",              lazy.spawn(screenshot_tool),                       desc="Screenshot"),
    Key([fn, "shift"], "c",     lazy.spawn("wal -i ~/.wallpapers"),                desc="Rerun pywal"),
    Key([mod], "space",         lazy.spawn(application_launcher + " -show drun"), desc="Launcher"),
    Key([mod], "g",             lazy.spawn(f"{browser} -new-tab https://gemini.google.com/app"), desc="Gemini"),

    Key([mod], "Right",         lazy.screen.next_group()),
    Key([mod], "Left",          lazy.screen.prev_group()),
    Key([fn], "f",              lazy.window.toggle_floating()),
    Key([mod], "n",             lazy.layout.maximize()),
    Key([mod], "m",             lazy.window.minimize()),
    Key([mod], "k",             lazy.window.kill()),
    Key([mod], "a",             lazy.layout.left()),
    Key([mod], "d",             lazy.layout.right()),
    Key([mod], "s",             lazy.layout.down()),
    Key([mod], "w",             lazy.layout.up()),
    Key([mod, "shift"], "a",    lazy.layout.grow_left()),
    Key([mod, "shift"], "d",    lazy.layout.grow_right()),
    Key([mod, "shift"], "s",    lazy.layout.grow_down()),
    Key([mod, "shift"], "w",    lazy.layout.grow_up()),
    Key([mod, "shift"], "q",    lazy.shutdown()),
    Key([mod, "shift"], "x",    lazy.shutdown()),
    Key([mod, "shift"], "r",    lazy.function(safe_restart)),
    Key([mod], "F12",           lazy.group["scratchpad"].dropdown_toggle("term")),
    Key([fn], "w",              lazy.function(change_wallpaper)),

    Key([fn, "shift"], "r",     lazy.function(reload_wal_colors), desc="Reload wal colors live"),
]

"""<<< ------------------------------------------------- WORKSPACES -------------------------------------------------- >>>"""

groups = [Group(str(i)) for i in range(1, 8)]

for i in groups:
    keys.extend([
        Key([mod], i.name,          lazy.group[i.name].toscreen()),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name)),
    ])

"""<<< --------------------------------------------------- LAYOUTS --------------------------------------------------- >>>"""

layouts = [
    layout.MonadTall(
        border_focus=PALETTE["accent"],
        border_normal=PALETTE["muted"],
        border_width=2,
        margin=8,
    ),
    layout.Max(),
]

"""<<< ------------------------------------------------- AUTO START -------------------------------------------------- >>>"""

@hook.subscribe.startup_once
def auto_start():
    wall_dir = os.path.expanduser("~/.wallpapers")
    if os.path.isdir(wall_dir):
        files = [f for f in os.listdir(wall_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if files:
            random_wall = os.path.join(wall_dir, random.choice(files))
            subprocess.Popen(["wal", "-i", random_wall])
    subprocess.Popen(["setxkbmap", "de"])
    subprocess.Popen(["eww", "daemon"])
    subprocess.Popen(["xrandr", "--output", "eDP-1", "--mode", "1920x1080", "--pos", "0x0"])

"""<<< ---------------------------------------------------- BAR ------------------------------------------------------ >>>"""

FONT  = "JetBrainsMono Nerd Font"
FSIZE = 13

def _gap(n=8):
    return widget.Spacer(length=n)

def _pipe(key):
    w = widget.TextBox(text="|", font=FONT, fontsize=FSIZE,
                       foreground=PALETTE["muted"], padding=4)
    _LIVE_WIDGETS[key] = w
    return w

def _icon(key, text, color_key):
    w = widget.TextBox(text=text, font=FONT, fontsize=FSIZE,
                       foreground=PALETTE[color_key], padding=4)
    _LIVE_WIDGETS[key] = w
    return w

def set_bar():
    p = PALETTE

    gbox = widget.GroupBox(
        font=FONT, fontsize=FSIZE, padding=6, borderwidth=2,
        highlight_method="line",
        this_current_screen_border=p["accent"],
        other_current_screen_border=p["purple"],
        this_screen_border=p["muted"],
        other_screen_border=p["muted"],
        highlight_color=[p["bg"], p["bg"]],
        active=p["fg"],
        inactive=p["muted"],
        urgent_border=p["alert"],
        background=p["bg"],
        disable_drag=True, rounded=False, use_mouse_wheel=False,
    )
    _LIVE_WIDGETS["groupbox"] = gbox

    wname = widget.WindowName(
        font=FONT, fontsize=FSIZE, foreground=p["muted"],
        max_chars=40, empty_group_string="",
    )
    _LIVE_WIDGETS["windowname"] = wname

    clk_time = widget.Clock(
        format="%H:%M", font=FONT, fontsize=16,
        foreground=p["accent"], padding=0,
    )
    _LIVE_WIDGETS["clock_time"] = clk_time

    clk_sep = widget.TextBox(
        text="  ", font=FONT, fontsize=FSIZE,
        foreground=p["muted"], padding=0,
    )
    _LIVE_WIDGETS["clock_sep"] = clk_sep

    clk_date = widget.Clock(
        format="%a %d.%m.%Y", font=FONT, fontsize=FSIZE,
        foreground=p["muted"], padding=0,
    )
    _LIVE_WIDGETS["clock_date"] = clk_date

    cpu = widget.CPU(
        font=FONT, fontsize=FSIZE, foreground=p["warn"],
        format="{load_percent:.0f}%", update_interval=2, padding=0,
    )
    _LIVE_WIDGETS["cpu"] = cpu

    mem = widget.Memory(
        font=FONT, fontsize=FSIZE, foreground=p["purple"],
        format="{MemPercent:.0f}%", update_interval=2, padding=0,
    )
    _LIVE_WIDGETS["mem"] = mem

    vol = widget.Volume(font=FONT, fontsize=FSIZE, foreground=p["fg"], padding=0)
    _LIVE_WIDGETS["vol"] = vol

    wifi = widget.Wlan(
        interface="wlan0", format="{essid}",
        disconnected_message="offline",
        font=FONT, fontsize=FSIZE, foreground=p["good"], padding=0,
    )
    _LIVE_WIDGETS["wifi"] = wifi

    bat = widget.Battery(
        font=FONT, fontsize=FSIZE,
        format="{char} {percent:2.0%}",
        charge_char="", discharge_char="",
        full_char="", unknown_char="?", empty_char="",
        low_percentage=0.2,
        low_foreground=p["alert"],
        foreground=p["good"],
        notify_below=20, padding=0,
    )
    _LIVE_WIDGETS["bat"] = bat

    notif_icon  = _icon("notif_icon",  "",   "muted")
    cpu_icon    = _icon("cpu_icon",    "",   "warn")
    mem_icon    = _icon("mem_icon",    "",   "purple")
    vol_icon    = _icon("vol_icon",    "",   "fg")
    wifi_icon   = _icon("wifi_icon",   "󰤨",   "good")

    blocks = (
        [_gap(10), gbox, _gap(6), _pipe("sep_title"), _gap(6), wname]
        + [widget.Spacer(), clk_time, clk_sep, clk_date, widget.Spacer()]
        + [
            notif_icon,         _pipe("sep_notif"),
            cpu_icon, cpu,      _gap(4),
            mem_icon, mem,      _pipe("sep_res"),
            vol_icon, vol,      _pipe("sep_vol"),
            wifi_icon, wifi,    _pipe("sep_wifi"),
            bat,                _pipe("sep_bat"),
            widget.CurrentLayoutIcon(scale=0.6, padding=4),
            _pipe("sep_layout"),
            widget.Systray(padding=6),
            _gap(10),
        ]
    )

    return [
        Screen(
            top=bar.Bar(
                blocks,
                28,
                background=p["bg"] + "E6",
                margin=[6, 10, 0, 10],
                border_width=0,
                opacity=1.0,
            ),
        )
    ]

screens = set_bar()

"""<<< ---------------------------------------------------- MOUSE ---------------------------------------------------- >>>"""

mouse = [
    Drag([mod],  "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod],  "Button3", lazy.window.set_size_floating(),     start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

"""<<< ------------------------------------------------- SCRATCHPAD -------------------------------------------------- >>>"""

groups.append(
    ScratchPad("scratchpad", [
        DropDown("term", terminal, width=0.6, height=0.6, x=0.2, y=0.1, opacity=0.9),
    ])
)

"""<<< ---------------------------------------------------- MAIN ----------------------------------------------------- >>>"""

dgroups_app_rules      = []
dgroups_key_binder     = None
dgroups_focus_by_rule  = False
dgroups_match_by_rule  = True
dgroups_repeat_once    = True

follow_mouse_focus   = True
bring_front_on_focus = False
cursor_warp          = False

floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class='confirm'),   Match(wm_class='dialog'),
        Match(wm_class='download'),  Match(wm_class='error'),
        Match(wm_class='file_progress'), Match(wm_class='notification'),
        Match(wm_class='splash'),    Match(wm_class='toolbar'),
        Match(wm_class='ssh-askpass'), Match(wm_class='pinentry'),
        Match(wm_class='confirmreset'),
        Match(title='makebranch'),   Match(title='maketag'),
        Match(title='branchdialog'), Match(title='pinentry'),
    ]
)

auto_fullscreen            = True
focus_on_window_activation = "smart"
reconfigure_screens        = True
auto_minimize              = True

wmname = "LG3D"