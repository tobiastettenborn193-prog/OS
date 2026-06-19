import os
import subprocess
import dotenv
from libqtile import hook

dotenv.load_dotenv("Hyperparameters.env")

# Optionales externes Shell-Skript
subprocess.Popen(["/home/tobster/.config/qtile/autostart.sh"])

@hook.subscribe.startup_once
def auto_start():
    wall_dir = os.path.expanduser("~/.wallpapers")
    if os.path.isdir(wall_dir):
        subprocess.run(["python3", "/home/tobster/os/qtile/scripts/pywal_change_theme.py"])

    subprocess.Popen(["picom", "-b"])

    # Dunst mit dem generierten Theme starten
    subprocess.run(["killall", "dunst"])
    subprocess.Popen(["dunst", "-config", os.path.expanduser("~/.cache/wal/dunstrc")])


    subprocess.run(["killall", "rustc", "cargo", "clangd", "clangd++"])
