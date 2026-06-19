import subprocess

def _get_volume_info():
    """Liest die aktuelle Lautstärke und den Mute-Status über Pipewire aus."""
    try:
        result = subprocess.run(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        is_muted = "[MUTED]" in output
        vol_str = output.replace("Volume:", "").replace("[MUTED]", "").strip()
        volume = int(float(vol_str) * 100)
        return volume, is_muted
    except Exception:
        return 0, False

def _show_notification(volume, is_muted):
    """Zeigt ein schickes On-Screen-Display über Dunst an."""
    if is_muted or volume == 0:
        icon = "audio-volume-muted"
        text = "Stummgeschaltet"
    elif volume < 30:
        icon = "audio-volume-low"
        text = f"{volume}%"
    elif volume < 70:
        icon = "audio-volume-medium"
        text = f"{volume}%"
    else:
        icon = "audio-volume-high"
        text = f"{volume}%"

    # WICHTIG: Hier Popen nutzen! Run würde Qtile einfrieren.
    subprocess.Popen([
        "notify-send",
        "-a", "Volume",
        "-i", icon,
        "-h", "string:x-dunst-stack-tag:volume",
        "-h", f"int:value:{volume}",
        "Lautstärke", text
    ])

def vol_up(qtile=None):
    """Erhöht die Lautstärke und zeigt das OSD."""
    subprocess.run(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", "5%+"])
    vol, muted = _get_volume_info()
    _show_notification(vol, muted)

def vol_down(qtile=None):
    """Verringert die Lautstärke und zeigt das OSD."""
    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"])
    vol, muted = _get_volume_info()
    _show_notification(vol, muted)

def vol_mute(qtile=None):
    """Schaltet stumm und zeigt das OSD."""
    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
    vol, muted = _get_volume_info()
    _show_notification(vol, muted)
