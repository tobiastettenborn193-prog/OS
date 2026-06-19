import json
import os
import random
import subprocess
import time

def change_wallpaper():
    wallpaper_dir = os.path.expanduser("~/.wallpapers")
    if not os.path.exists(wallpaper_dir): return

    files = os.listdir(wallpaper_dir)
    if not files: return

    random_file = random.choice(files)
    full_path = os.path.join(wallpaper_dir, random_file)
    subprocess.run(["wal", "-q", "-i", full_path])

def change_theme():
    pywal_file = os.path.expanduser("~/.cache/wal/colors.json")
    env_path = os.path.expanduser("~/os/qtile/env/system_colors.env")

    if not os.path.exists(pywal_file): return

    with open(pywal_file, "r") as f:
        wal = json.load(f)

    # Entschärftes Mapping der Farben
    env_content = f"""
TIMESTAMP={int(time.time())}

# Base
BAR_BG={wal["special"]["background"]}
TEXT_FG={wal["special"]["foreground"]}
TEXT_MUTED={wal["colors"]["color8"]}
SEP_COLOR={wal["colors"]["color8"]}

# accents
ACCENT_ACTIVE={wal["colors"]["color4"]}
ACCENT_INACTIVE={wal["colors"]["color5"]}

# widgets
LOGO_COLOR={wal["colors"]["color4"]}
CLOCK_COLOR={wal["colors"]["color7"]}
CPU_RAM_COLOR={wal["colors"]["color3"]}
AUDIO_COLOR={wal["colors"]["color6"]}
LAYOUT_COLOR={wal["colors"]["color5"]}
"""
    os.makedirs(os.path.dirname(env_path), exist_ok=True)

    with open(env_path, "w") as f:
        f.write(env_content)

if __name__ == "__main__":
    change_wallpaper()
    change_theme()
