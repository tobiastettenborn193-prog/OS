"""<<< ---------------------------------------------------- SETUP ---------------------------------------------------- >>>"""
 
"""
Execute the command "mkdir -p ~/.config/qtile" to create the qtile configuration directory.
Then copy this file to ~/.config/qtile/config.py
Execute the command "chmod +x ~/.config/qtile/config.py" to make the file executable.
Finally, restart qtile with "qtile restart".
"""
 
"""<<< --------------------------------------------------- IMPORTS --------------------------------------------------- >>>"""
 
import os
import json
import random
import subprocess
from libqtile import layout, widget, bar, hook
from libqtile.config import Group, Key, Screen, ScratchPad, DropDown, Match, Drag, Click
try:
    from libqtile.lazy import lazy          # Qtile 0.21+
except ImportError:
    from libqtile.command import lazy       # Qtile <= 0.20
 
"""<<< ----------------------------------------------- HYPERPARAMETERS ----------------------------------------------- >>>"""
 
# superkey
mod = "mod4"
# alt key
fn = "mod1"
# hash symbol bypass (avoids f-string issues)
hash_sym = chr(35)
 
# terminal
terminal = "alacritty"
# browser
browser = "zen-browser"
# file manager
file_manager = "thunar"
# screenshot
screenshot_tool = "spectacle"
# power menu
power_menu = "eww"
# application launcher
application_launcher = "rofi"
# background manager
background_manager = "feh"
 
"""<<< -------------------------------------------------- FUNCTIONS -------------------------------------------------- >>>"""
 
def change_wallpaper(qtile=None):
    wall_dir = os.path.expanduser("~/.wallpapers")
    os.makedirs(wall_dir, exist_ok=True)
 
    files = [f for f in os.listdir(wall_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if not files:
        return
 
    wallpaper_choice = random.choice(files)
    full_path = os.path.join(wall_dir, wallpaper_choice)

    # Fixed: just set the wallpaper directly without reloading the entire config
    subprocess.Popen(["wal", "-i", full_path])
 
 
def safe_restart(qtile):
    """
    Version-safe restart: tries reload_config() first (Qtile 0.21+),
    falls back to restart() for older versions.
    """
    try:
        qtile.reload_config()
    except AttributeError:
        qtile.restart()
 
"""<<< ------------------------------------------------- KEYBINDINGS ------------------------------------------------- >>>"""
 
keys = [
 
    # -------- Applications --------
 
    # Launch terminal
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    # Launch browser
    Key([mod], "BackSpace", lazy.spawn(browser), desc="Launch browser"),
    # Launch file manager
    Key([mod], "f", lazy.spawn(file_manager), desc="Launch file manager"),
    # Launch power menu
    Key([mod, fn], "p", lazy.spawn(power_menu), desc="Launch power menu"),
    # Launch screenshot tool
    Key([fn], "p", lazy.spawn(screenshot_tool), desc="Launch screenshot tool"),
    # Launch color scenario (pywal)
    Key([fn, "shift"], "c", lazy.spawn("wal -i ~/.wallpapers"), desc="Rerun pywal"),
    # Launch application launcher
    Key([mod], "space", lazy.spawn(application_launcher + " -show drun"), desc="Launch rofi"),
    # Launch gemini
    Key([mod], "g", lazy.spawn(f"{browser} -new-tab https://gemini.google.com/app"), desc="Launch Gemini"),
 
    # -------- Window Management --------
 
    # change workspace (right / left)
    Key([mod], "Right", lazy.screen.next_group(), desc="Next workspace"),
    Key([mod], "Left",  lazy.screen.prev_group(), desc="Previous workspace"),
    # toggle floating
    Key([fn], "f", lazy.window.toggle_floating(), desc="Float window"),
    # maximize in layout (MonadTall only — no-op in Max layout, no crash)
    Key([mod], "n", lazy.layout.maximize(), desc="Maximize in layout"),
    # minimize window
    Key([mod], "m", lazy.window.minimize(), desc="Minimize window"),
    # close window
    Key([mod], "k", lazy.window.kill(), desc="Close window"),
    # focus navigation (hjkl-style: a=left, d=right, w=up, s=down)
    Key([mod], "a", lazy.layout.left(),  desc="Focus left"),
    Key([mod], "d", lazy.layout.right(), desc="Focus right"),
    Key([mod], "s", lazy.layout.down(),  desc="Focus down"),
    Key([mod], "w", lazy.layout.up(),    desc="Focus up"),
    # resize
    Key([mod, "shift"], "a", lazy.layout.grow_left(),  desc="Resize left"),
    Key([mod, "shift"], "d", lazy.layout.grow_right(), desc="Resize right"),
    Key([mod, "shift"], "s", lazy.layout.grow_down(),  desc="Resize down"),
    Key([mod, "shift"], "w", lazy.layout.grow_up(),    desc="Resize up"),
    # quit qtile
    Key([mod, "shift"], "q", lazy.shutdown(), desc="Quit Qtile"),
    Key([mod, "shift"], "x", lazy.shutdown(), desc="Quit Qtile (alt)"),
 
    # -------- System Management --------
 
    # restart qtile — version-safe via lazy.function
    Key([mod, "shift"], "r", lazy.function(safe_restart), desc="Restart Qtile (version-safe)"),
    # scratchpad — on F12 to avoid conflict with [mod]+s (focus down)
    Key([mod], "F12", lazy.group["scratchpad"].dropdown_toggle("term"), desc="Toggle ScratchPad"),
    # change wallpaper
    Key([fn], "w", lazy.function(change_wallpaper), desc="Change wallpaper"),
]
 
"""<<< ---------------------------------------------------- PYWAL ---------------------------------------------------- >>>"""
 
wal_file = os.path.expanduser("~/.cache/wal/colors.json")
 
def get_color_scheme():
    if os.path.exists(wal_file):
        try:
            with open(wal_file) as f:
                wal = json.load(f)
            return wal.get("colors")
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    return None
 
colors = get_color_scheme() or {
    'color0': f'{hash_sym}000000',
    'color1': f'{hash_sym}ff0000',
    'color2': f'{hash_sym}00ff00',
    'color3': f'{hash_sym}ffff00',
    'color4': f'{hash_sym}0000ff',
    'color7': f'{hash_sym}ffffff',
    'color8': f'{hash_sym}444444',
}
 
"""<<< ------------------------------------------------- WORKSPACES -------------------------------------------------- >>>"""
 
groups = [Group(str(i)) for i in range(1, 8)]
 
for i in groups:
    keys.extend([
        Key([mod], i.name, lazy.group[i.name].toscreen(), desc=f"Switch to workspace {i.name}"),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name), desc=f"Move window to workspace {i.name}"),
    ])
 
"""<<< --------------------------------------------------- LAYOUTS --------------------------------------------------- >>>"""
 
layouts = [
    layout.MonadTall(
        border_focus=f"{hash_sym}ff0000",
        border_normal=f"{hash_sym}333333",
        border_width=4,
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

FONT_PARAMS = {
    "font": "JetBrainsMono Nerd Font",
    "fontsize": 13,
    "padding": 4,
}

def _sep():
    return widget.Sep(linewidth=2, foreground=colors['color8'], padding=6)

def set_bar():
    blocks = [
        # ◢■■■ GroupBox with decorative markers ■■■◤
        widget.TextBox(
            text="◢", fontsize=50, padding=-1,
            font="Arial", foreground=colors['color0'],
        ),
        widget.GroupBox(
            highlight_method="line",
            this_current_screen_border=colors['color4'],
            other_current_screen_border=colors['color1'],
            this_screen_border=colors['color4'],
            other_screen_border=colors['color1'],
            highlight_color=colors['color4'],
            urgent_border=colors['color1'],
            active=colors['color7'],
            inactive=colors['color8'],
            background=colors['color0'],
            disable_drag=True,
            borderwidth=2,
            **FONT_PARAMS,
        ),
        widget.TextBox(
            text="◤ ", fontsize=50, padding=-5,
            font="Arial", foreground=colors['color0'],
        ),

        # Focused window title
        widget.WindowName(foreground=colors['color4'], **FONT_PARAMS),

        _sep(),

        # Resource graphs
        widget.CPUGraph(
            border_color=colors['color3'],
            graph_color=colors['color3'],
            border_width=1, line_width=1,
            type="line", width=50,
        ),
        widget.MemoryGraph(
            border_color=colors['color4'],
            graph_color=colors['color4'],
            border_width=1, line_width=1,
            type="line", width=50,
        ),
        widget.NetGraph(
            border_color=colors['color2'],
            graph_color=colors['color2'],
            border_width=1, line_width=1,
            type="line", width=50,
        ),

        _sep(),

        # Volume
        widget.TextBox("", foreground=colors['color7'], **FONT_PARAMS),
        widget.Volume(foreground=colors['color7'], **FONT_PARAMS),

        _sep(),

        # WiFi
        widget.TextBox("", foreground=colors['color2'], **FONT_PARAMS),
        widget.Wlan(
            interface="wlan0",
            format="{essid} {percent:2.0%}",
            disconnected_message="offline",
            foreground=colors['color2'],
            **FONT_PARAMS,
        ),

        _sep(),

        # Battery
        widget.Battery(
            format="{char} {percent:2.0%}",
            charge_char="",
            discharge_char="",
            full_char="",
            unknown_char="",
            empty_char="",
            low_percentage=0.2,
            low_foreground=colors['color1'],
            foreground=colors['color2'],
            notify_below=20,
            **FONT_PARAMS,
        ),

        _sep(),

        # Current layout icon
        widget.CurrentLayoutIcon(padding=4),

        _sep(),

        # Systray + Clock
        widget.Systray(padding=4),
        widget.Clock(
            format="%H:%M | %d.%m.%Y",
            foreground=colors['color7'],
            **FONT_PARAMS,
        ),
    ]

    return [
        Screen(
            top=bar.Bar(
                blocks,
                30,
                background=colors['color0'] + "CC",
                margin=[5, 10, 0, 10],
                opacity=0.9,
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
 
dgroups_app_rules    = []
dgroups_key_binder   = None
dgroups_focus_by_rule  = False
dgroups_match_by_rule  = True
dgroups_repeat_once    = True
 
follow_mouse_focus   = True
bring_front_on_focus = False
cursor_warp          = False
 
floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class='confirm'),
        Match(wm_class='dialog'),
        Match(wm_class='download'),
        Match(wm_class='error'),
        Match(wm_class='file_progress'),
        Match(wm_class='notification'),
        Match(wm_class='splash'),
        Match(wm_class='toolbar'),
        Match(wm_class='ssh-askpass'),
        Match(wm_class='pinentry'),
        Match(wm_class='confirmreset'),
        Match(title='makebranch'),
        Match(title='maketag'),
        Match(title='branchdialog'),
        Match(title='pinentry'),
    ]
)
 
auto_fullscreen          = True
focus_on_window_activation = "smart"
reconfigure_screens      = True
auto_minimize            = True
 
wmname = "LG3D"