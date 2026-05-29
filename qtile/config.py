#<<< ---------------------------- SETUP ---------------------------- >>>>#

"""
Execute the command "mkdir -p ~/.config/qtile" to create the qtile configuration directory.
Then copy this file to ~/.config/qtile/config.py || cd ~/.config/qtile && touch config.py.
Execute the command "chmod +x ~/.config/qtile/config.py" to make the file executable.

Finally, restart qtile with "qtile restart".

"""

#<<< ---------------------------- IMPORTS ---------------------------- >>>>#

import os
import json
import random
import time
import subprocess
from libqtile import layout, widget, bar, hook
from libqtile.config import Group, Key, Screen, ScratchPad, DropDown, Match, Drag, Click
from libqtile.command import lazy


#<<< ---------------------------- HYPERPARAMETERS ---------------------------- >>>>#

#---------SYSTEM---------#

#superkey
mod = "mod4"
#function key
fn = "mod1"


#---------APPLICATIONS---------#

#terminal
terminal = "alacritty"
#browser
browser = "zen-browser"
#file manager
file_manager = "thunar"
#screenshot
screenshot_tool = "spectacle"
#power menu
power_menu = "Eww"
#color_scenario 
color_scenario = "Pywal"
#application launcher
application_launcher = "rofi"
#background
background_manager = "feh"


#<<<---------------------------- KEYBINDINGS ---------------------------- >>>>#

keys = [

    #--------Applications--------#

    # Launch terminal
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    # Launch browser
    Key([mod, "backspace"], lazy.spawn(browser), desc="Launch browser"),
    # Launch file manager
    Key([mod, "b"], lazy.spawn(file_manager), desc="Launch file manager"),
    # Launch power menu
    Key([mod, fn], lazy.spawn(power_menu), desc="Launch power menu"),
    # Launch screenshot tool
    Key([fn, "p"], lazy.spawn(screenshot_tool), desc="Launch screenshot tool"),
    # Launch color scenario
    Key([fn, "shift"], lazy.spawn(color_scenario), desc="Launch color scenario"),
    # Launch application launcher
    Key([mod], "space", lazy.spawn(application_launcher + " -show drun"), desc="Launch rofi"),
    #Launch gemini
    Key([mod, "#"], lazy.spawn(f"{browser} -new-tab https://gemini.google.com/app")),
    
    

    #--------Window Management--------#

    #change workspace(right)
    Key([mod], "Right", lazy.screen.next_group()),
    #change workspace(left)
    Key([mod], "Left", lazy.screen.prev_group()),
    #float window
    Key([mod, "left_alt"], lazy.window.toggle_floating(), desc="Float window"), 
    #maximize window
    Key([mod, "n"], lazy.window.toggle_maximize(), desc="Maximize window"),   
    #minimize window
    Key([mod, "m"], lazy.window.toggle_minimize(), desc="Minimize window"),   
    #close window
    Key([mod, "k"], lazy.window.kill(), desc="Close window"),
    #move window left
    Key([mod, "a"], lazy.layout.left(), desc="Move window left"),
    #move window right
    Key([mod, "d"], lazy.layout.right(), desc="Move window right"),
    #move window up
    Key([mod, "s"], lazy.layout.down(), desc="Move window down"),
    #move window down
    Key([mod, "w"], lazy.layout.up(), desc="Move window up"),
    #resize window left
    Key([mod, "shift", "a"], lazy.layout.grow_left(), desc="Resize window left"),
    #resize window right
    Key([mod, "shift", "d"], lazy.layout.grow_right(), desc="Resize window right"),
    #resize window up
    Key([mod, "shift", "s"], lazy.layout.grow_down(), desc="Resize window down"),
    #resize window down
    Key([mod, "shift", "w"], lazy.layout.grow_up(), desc="Resize window up"),
    #kill all aplications
    Key([mod, "shift", "q"], lazy.shutdown(), desc="Kill all applications"),

    #--------System Management--------#

    #restart qtile
    Key([mod, "shift", "r"], lazy.restart(), desc="Restart Qtile"),
    #quit qtile
    Key([mod, "shift", "x"], lazy.shutdown(), desc="Quit Qtile"),
    #Scratchpad
    Key([mod], "s", lazy.group["scratchpad"].dropdown_toggle("term"), desc="Toggle ScratchPad"),
    #change wallpaper
    Key([fn, "c"], lazy.function(change_wallpaper), desc="Change wallpaper"),
]

#<<<---------------------------- PYWAL ---------------------------- >>>>

wal_file = os.path.expanduser("~/.cache/wal/colors.json")

def get_color_scheme():
    if os.path.exists(wal_file):
        with open(wal_file) as f:
            wal = json.load(f)
        return wal["colors"]
    return None

colors = get_color_scheme() or {
    'color0': '#000000', 'color1': '#ff0000', 'color4': '#0000ff', 
    'color7': '#ffffff', 'color8': '#444444'
}




#<<<---------------------------- WORKSPACES ---------------------------- >>>>#

groups = [Group(str(i)) for i in range(1, 8)]

for i in groups:
    keys.extend([
        Key([mod], i.name, lazy.group[i.name].toscreen()),
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name))
    ])

#<<<---------------------------- LAYOUTS ---------------------------- >>>>#

layouts = [
    layout.MonadTall(border_focus="#ff0000", border_normal="#333333", border_width=4, margin=8),
    layout.Max(),
]

#<<<---------------------------- BACKGROUND ---------------------------- >>>>#

def change_wallpaper(qtile=None):
    wall_dir = os.path.expanduser("~/.wallpapers")
    os.makedirs(wall_dir, exist_ok=True)
    

    files = [f for f in os.listdir(wall_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if not files:
        return

    wallpaper_choice = random.choice(files)
    full_path = os.path.join(wall_dir, wallpaper_choice)
    
    
    subprocess.run(["wal", "-i", full_path])
    time.sleep(0.5)
    
    
    if qtile is not None:
        qtile.reload_config()

#<<<---------------------------- Auto start ---------------------------- >>>>

@hook.subscribe.startup_once
def auto_start():
    #Wallpaper and Pywal
    wall_dir = os.path.expanduser("~/.wallpapers")
    files = [f for f in os.listdir(wall_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if files:
        random_wall = os.path.join(wall_dir, random.choice(files))
        # Nutze Popen, damit Qtile sofort weiter startet
        subprocess.Popen(["wal", "-i", random_wall])
        subprocess.Popen(["feh", "--bg-scale", random_wall])

    #System-Tools
    subprocess.Popen(["setxkbmap", "de"])
    subprocess.Popen(["picom", "--config", os.path.expanduser("~/.config/picom/picom.conf")])
    subprocess.Popen(["eww", "daemon"])
    #Keyboard Layout
    subprocess.Popen(["xrandr", "--output", "eDP-1", "--mode", "1920x1080", "--pos", "0x0"])

#<<<---------------------------- Waybar ---------------------------- >>>>#

def set_waybar():
    screens = [
        Screen(
            top=bar.Bar(
                [
                    widget.GroupBox(
                        highlight_method='line',
                        this_current_screen_border=colors['color4'],
                        active=colors['color7'],
                        inactive=colors['color8'],
                    ),
                    widget.Spacer(length=20),
                    widget.WindowName(foreground=colors['color4']),
                    widget.Systray(),
                    widget.Clock(format='%H:%M | %d.%m.%Y', foreground=colors['color7']),
                ],
                30,
                background=colors['color0'] + "CC",
                margin=[5, 10, 0, 10],
                opacity=0.8,
            ),
        ),
    ]
    return screens

screens = set_waybar()



#<<<---------------------------- MOUSE ---------------------------- >>>>#

mouse = [
    mouse.Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    mouse.Drag([mod], "Button3", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    mouse.Click([mod], "Button2", lazy.window.bring()),
]

#<<<------------------------------Scratchpad----------------------------- >>>>#

groups.append(
    ScratchPad("scratchpad", [
        DropDown("term", terminal, width=0.6, height=0.6, x=0.2, y=0.1, opacity=0.9),
    ])
)

#<<<------------------------------Main------------------------------------->>>>#

dgroups_app_rules = []  
dgroups_key_binder = None
dgroups_focus_by_rule = False
dgroups_match_by_rule = True
dgroups_repeat_once = True

main = None
follow_mouse_focus = True
bring_front_on_focus = False
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wmclass='confirm'),
        Match(wmclass='dialog'),
        Match(wmclass='download'),
        Match(wmclass='error'),
        Match(wmclass='file_progress'),
        Match(wmclass='notification'),
        Match(wmclass='splash'),
        Match(wmclass='toolbar'),
        Match(title='makebranch'),
        Match(title='maketag'),
        Match(wmclass='ssh-askpass'),
        Match(title='branchdialog'),
        Match(title='pinentry'),
        Match(wmclass='pinentry'),
        Match(wmclass='confirmreset'),
        Match(title='makebranch'),
        Match(title='maketag'),
        Match(wmclass='ssh-askpass'),
        Match(title='branchdialog'),
        Match(title='pinentry'),
        Match(wmclass='pinentry'),
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

auto_minimize = True


wmname = "LG3D"