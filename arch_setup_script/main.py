import os
import sys 
import subprocess

#<<<-----------------------------------------------------------HYPERPARAMETERS---------------------------------------------------------->>>

picom_content = """
# Backend & Performance
backend = "glx";
glx-no-stencil = true;
glx-no-rebind-pixmap = true;
vsync = true;
use-damage = true;

# Corners (The Hyprland Look)
corner-radius = 12;
rounded-corners-exclude = [
  "window_type = 'dock'",
  "window_type = 'desktop'"
];

# Fading (Smooth transitions)
fading = true;
fade-in-step = 0.03;
fade-out-step = 0.03;
fade-delta = 5;

# Shadows (Minimal & Resource Saving)
shadow = false;

# Opacity (Subtle transparency for terminals/launchers)
inactive-opacity = 0.93;
frame-opacity = 1.0;
inactive-opacity-override = false;
active-opacity = 1.0;

focus-exclude = [
  "class_g = 'Cairo-clock'",
  "window_type = 'desktop'"
];

opacity-rule = [
  "100:class_g = 'Steam'",
  "100:class_g = 'zen-browser'",
  "95:class_g = 'Alacritty'",
  "95:class_g = 'Rofi'"
];

# General Settings
wintypes:
{
  tooltip = { fade = true; shadow = false; opacity = 0.85; focus = true; full-shadow = false; };
  dock = { shadow = false; clip-shadow-above = true; };
  dnd = { shadow = false; };
  popup_menu = { opacity = 0.95; };
  dropdown_menu = { opacity = 0.95; };
};
"""

# Picom via autostart.sh, Pipewire via systemd symlinks
autostart_content = """#!/bin/bash
picom --config ~/.config/picom/picom.conf &
"""

xinitrc_content = """#!/bin/bash
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax --exit-with-session)
fi
xhost +local: &> /dev/null
exec qtile start
"""

# pywal postscript — triggers reload_wal_colors() in qtile via IPC after every wal run
wal_postscript_content = """#!/bin/bash
sleep 0.3
qtile cmd-obj -o cmd -f execute_custom_command -a "reload_wal_colors" 2>/dev/null
if [ $? -ne 0 ]; then
    qtile-cmd -o cmd -f execute_custom_command -a "reload_wal_colors" 2>/dev/null
fi
"""

# pywal postscript — rewrites the starship palette section after every wal run
starship_wal_postscript_content = """#!/bin/bash
source ~/.cache/wal/colors.sh

cat > ~/.config/starship_palette.toml << EOF
[palettes.wal]
color0 = "$color0"
color1 = "$color1"
color2 = "$color2"
color3 = "$color3"
color4 = "$color4"
color5 = "$color5"
color6 = "$color6"
color7 = "$color7"
EOF
"""

# Main starship config — palette is loaded from starship_palette.toml via !include
starship_content = """
"$schema" = 'https://starship.rs/config-schema.json'

palette = "wal"

# Palette wird von ~/.config/wal/postscripts/starship_reload.sh nach jedem wal-Run neu geschrieben
[palettes.wal]
color0 = "#1a1a2e"
color1 = "#e06c75"
color2 = "#98c379"
color3 = "#e5c07b"
color4 = "#61afef"
color5 = "#c678dd"
color6 = "#56b6c2"
color7 = "#abb2bf"

format = \"\"\"
[┌─](color7)$directory$git_branch$git_status$git_metrics
[└─](color7)$python$rust$nodejs$cmd_duration$character\"\"\"

[directory]
style = "bold color4"
truncation_length = 3
truncate_to_repo = true
format = "[ $path ]($style)[$read_only]($read_only_style) "

[git_branch]
symbol = " "
style = "color5"
format = "[on](color7) [$symbol$branch]($style) "

[git_status]
style = "color1"
format = '([$all_status$ahead_behind]($style) )'
conflicted = "⚡"
ahead = "⇡${count}"
behind = "⇣${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
modified = "✎${count}"
untracked = "?${count}"
staged = "+${count}"
deleted = "✘${count}"

[git_metrics]
added_style = "color2"
deleted_style = "color1"
format = '([+$added]($added_style) )([-$deleted]($deleted_style) )'
disabled = false

[python]
symbol = " "
style = "color3"
format = '[${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'

[rust]
symbol = " "
style = "color1"
format = '[$symbol($version )]($style)'

[nodejs]
symbol = " "
style = "color2"
format = '[$symbol($version )]($style)'

[cmd_duration]
min_time = 2_000
style = "color3"
format = "[⏱ $duration]($style) "

[character]
success_symbol = "[❯](color2)"
error_symbol = "[❯](color1)"
"""

timeout = 3000
terminal = "alacritty"
browser = "zen-browser"
power_menu = "eww"
application_launcher = "rofi"
file_manager = "thunar"

failed_packages = []

before_download = ["networkmanager", "git", "base-devel", "archlinux-keyring", "rust", "cargo"]

download_list = [
    "zsh", "starship", terminal, browser, power_menu, application_launcher, file_manager,
    "picom", "lib32-libva-mesa-driver", "libva-mesa-driver", "lib32-vulkan-radeon",
    "vulkan-radeon", "xf86-video-amdgpu", "xorg-server", "xorg-xinit", "xorg-xauth",
    "mesa", "xf86-input-libinput", "python", "uv", "nano", "rust-analyzer", "windsurf-bin",
    "steam", "vesktop", "qtile", "pipewire", "pipewire-pulse", "pipewire-alsa",
    "pipewire-jack", "htop", "fastfetch", "spectacle", "dunst", "feh", "polkit-gnome",
    "wireplumber", "pavucontrol", "ttf-jetbrains-mono-nerd", "unzip", "python-pywal",
    "bluez", "bluez-utils",
]

#<<<-----------------------------------------------------------FUNCTIONS---------------------------------------------------------->>>

def execute_command(command: str):
    try:
        result = subprocess.run(
            command, shell=True, check=True,
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout}s: {command}")
        raise
    except subprocess.CalledProcessError as e:
        # stderr weitergeben damit Aufrufer es loggen können
        raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, e.stderr)

def smart_download_package(package):
    print(f"\nTrying to install package: {package}")
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
        print(f"-> {package} successfully installed via pacman.")
        return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"Pacman failed for {package}. Trying yay...")
    try:
        execute_command(f"su - tobster -c 'HOME=/home/tobster yay -S --needed --noconfirm {package}'")
        print(f"-> {package} successfully installed via yay.")
        return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"Yay failed for {package}. Trying Flatpak...")
    try:
        search_output = execute_command(f"flatpak search --columns=application {package}")
        if search_output.strip():
            flatpak_id = search_output.split("\n")[0].strip()
            execute_command(f"flatpak install -y flathub {flatpak_id}")
            print(f"-> {package} successfully installed via flatpak ({flatpak_id}).")
            return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"Flatpak installation failed for {package}.")
    failed_packages.append(package)
    print(f"Error: '{package}' could not be installed anywhere.")

def pacman_install(package):
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Pacman failed for {package}: {getattr(e, 'stderr', '')}")
        failed_packages.append(package)

def yay_install(package):
    try:
        execute_command(f"su - tobster -c 'HOME=/home/tobster yay -S --needed --noconfirm {package}'")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Yay failed for {package}: {getattr(e, 'stderr', '')}")
        failed_packages.append(package)

def flatpak_install(package):
    try:
        execute_command(f"flatpak install -y flathub {package}")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Flatpak failed for {package}: {getattr(e, 'stderr', '')}")
        failed_packages.append(package)

def clone_git(url, dest="/tmp/cloned_repo"):
    return execute_command(f"git clone {url} {dest}")

def install_before_packages():
    for package in before_download:
        pacman_install(package)
    print("\nBuilding yay manually from AUR...")
    try:
        execute_command("rm -rf /tmp/yay")
        execute_command("git clone https://aur.archlinux.org/yay.git /tmp/yay")
        execute_command("chown -R tobster:tobster /tmp/yay")
        execute_command("su - tobster -c 'cd /tmp/yay && HOME=/home/tobster makepkg -si --noconfirm'")
        print("-> yay successfully installed.")
    except subprocess.CalledProcessError as e:
        print(f"Critical error: yay could not be built.\nstdout: {e.output}\nstderr: {e.stderr}")
        failed_packages.append("yay")
    except subprocess.TimeoutExpired:
        print("Critical error: yay build timed out.")
        failed_packages.append("yay")

def install_packages():
    for package in download_list:
        smart_download_package(package)

def install_oh_my_zsh():
    # oh-my-zsh hat keinen pacman/AUR-Paketnamen, wird via Installer-Script installiert
    print("\nInstalling oh-my-zsh...")
    try:
        execute_command(
            "su - tobster -c '"
            "HOME=/home/tobster RUNZSH=no CHSH=no "
            'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
            "'"
        )
        print("-> oh-my-zsh installed.")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"oh-my-zsh install failed: {getattr(e, 'stderr', '')}")
        failed_packages.append("oh-my-zsh")

def qtile_config():
    url = "https://github.com/tobiastettenborn193-prog/OS.git"
    clone_git(url, "/tmp/OS_config")
    execute_command("mkdir -p /home/tobster/.config/qtile")
    execute_command("cp /tmp/OS_config/qtile/config.py /home/tobster/.config/qtile/")
    execute_command("chmod +x /home/tobster/.config/qtile/config.py")
    execute_command("mkdir -p /home/tobster/.wallpapers")
    execute_command("chown -R tobster:tobster /home/tobster/.config /home/tobster/.wallpapers")

def setup_system_basics():
    try:
        execute_command("sed -i '/\\[multilib\\]/,+1 s/^#//' /etc/pacman.conf")
        execute_command("pacman -Syy")
        execute_command("pacman -S --needed --noconfirm flatpak")
        execute_command("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo")
        print("-> Multilib + Flathub enabled.")
    except subprocess.CalledProcessError:
        print("Failed to enable multilib/flatpak.")
    try:
        execute_command("useradd -m -G wheel -s /bin/zsh tobster")
        execute_command("echo 'tobster:password' | chpasswd")
        execute_command("sed -i 's/# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
        print("-> User 'tobster' created and sudo access configured.")
    except subprocess.CalledProcessError:
        print("Failed to create user or setup sudo (user may already exist).")
    try:
        execute_command("systemctl enable NetworkManager")
        print("-> NetworkManager service enabled.")
    except subprocess.CalledProcessError:
        print("Failed to enable NetworkManager.")

def picom_config():
    config_dir = "/home/tobster/.config/picom"
    execute_command(f"mkdir -p {config_dir}")
    with open(f"{config_dir}/picom.conf", "w") as f:
        f.write(picom_content)
    execute_command("chown -R tobster:tobster /home/tobster/.config/picom")
    print("-> Picom configuration installed.")

def detect_wifi_interface():
    print("\nDetecting WiFi interface...")
    try:
        output = execute_command("ip link show")
        interface = None
        for line in output.splitlines():
            if ": wlan" in line or ": wlp" in line:
                interface = line.split(": ")[1].split(":")[0].strip()
                break
        if interface:
            config_path = "/home/tobster/.config/qtile/config.py"
            execute_command(f"sed -i 's/interface=\"wlan0\"/interface=\"{interface}\"/' {config_path}")
            print(f"-> WiFi interface '{interface}' patched into qtile config.")
        else:
            print("-> No WiFi interface found, leaving 'wlan0' as default.")
    except subprocess.CalledProcessError:
        print("-> Could not detect WiFi interface, leaving 'wlan0' as default.")

def autostart():
    autostart_path = "/home/tobster/.config/qtile/autostart.sh"
    with open(autostart_path, "w") as f:
        f.write(autostart_content)
    execute_command(f"chmod +x {autostart_path}")

    try:
        with open("/home/tobster/.xinitrc", "w") as f:
            f.write(xinitrc_content)
        execute_command("chmod +x /home/tobster/.xinitrc")
        print("-> .xinitrc configured.")
    except Exception as e:
        print(f"Failed to create .xinitrc: {e}")

    postscript_dir = "/home/tobster/.config/wal/postscripts"
    execute_command(f"mkdir -p {postscript_dir}")

    with open(f"{postscript_dir}/qtile_reload.sh", "w") as f:
        f.write(wal_postscript_content)
    execute_command(f"chmod +x {postscript_dir}/qtile_reload.sh")
    print("-> pywal postscript (qtile) installed.")

    with open(f"{postscript_dir}/starship_reload.sh", "w") as f:
        f.write(starship_wal_postscript_content)
    execute_command(f"chmod +x {postscript_dir}/starship_reload.sh")
    print("-> pywal postscript (starship) installed.")

    execute_command("chown -R tobster:tobster /home/tobster")

def setup_pipewire():
    # systemctl --user enable funktioniert nicht im Install-Kontext ohne laufende DBus-Session
    # Stattdessen: Symlinks manuell setzen wie systemctl --user enable es tun würde
    service_dir = "/home/tobster/.config/systemd/user"
    wants_dir = f"{service_dir}/default.target.wants"
    execute_command(f"mkdir -p {wants_dir}")

    for service in ["pipewire.service", "pipewire-pulse.service", "wireplumber.service"]:
        execute_command(
            f"ln -sf /usr/lib/systemd/user/{service} {wants_dir}/{service}"
        )

    execute_command("chown -R tobster:tobster /home/tobster/.config/systemd")
    print("-> Pipewire user services enabled via symlinks.")

def setup_zsh():
    # Pfad korrigiert: zshrc kommt aus dem geclonten Repo in /tmp/OS_config
    zshrc_src = "/tmp/OS_config/zsh/zsh.zshrc"
    zshrc_dst = "/home/tobster/.zshrc"
    try:
        execute_command(f"cp {zshrc_src} {zshrc_dst}")
        execute_command(f"chown tobster:tobster {zshrc_dst}")
        print("-> Zsh configured.")
    except subprocess.CalledProcessError:
        print(f"Warning: Could not copy zshrc from {zshrc_src} — file may not exist in repo.")

def setup_starship():
    config_dir = "/home/tobster/.config"
    execute_command(f"mkdir -p {config_dir}")
    with open(f"{config_dir}/starship.toml", "w") as f:
        f.write(starship_content)
    execute_command(f"chown tobster:tobster {config_dir}/starship.toml")
    print("-> Starship configured (pywal palette will update on first wal run).")

def load_wallpapers_to_folders():
    execute_command("mkdir -p /home/tobster/.wallpapers")
    execute_command("git clone https://github.com/phenax/wallpapers.git /home/tobster/.wallpapers")
    print("-> Wallpapers loaded.")

def setup_bluetooth():
    execute_command("systemctl enable bluetooth.service")
    print("-> Bluetooth service enabled.")

def setup_networkmanager():
    execute_command("systemctl enable NetworkManager.service")
    print("-> NetworkManager service enabled.")

#def setup_ly():
#   pacman_install("ly")
#  execute_command("systemctl enable ly.service")
#    print("-> Ly display manager enabled.")

#<<<-----------------------------------------------------------MAIN---------------------------------------------------------->>>

def main():
    setup_system_basics()
    install_before_packages()
    install_packages()
    install_oh_my_zsh()
    qtile_config()
    detect_wifi_interface()
    picom_config()
    load_wallpapers_to_folders()
    setup_pipewire()
    setup_bluetooth()
    setup_networkmanager()
    #setup_ly()
    setup_zsh()
    setup_starship()
    autostart()

    print("\n--- Process Finished ---")
    if failed_packages:
        print(f"Failed to install: {', '.join(failed_packages)}")
    else:
        print("Everything successfully installed! Reboot and log in via Ly.")

if __name__ == "__main__":
    main()