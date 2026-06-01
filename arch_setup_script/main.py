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

timeout = 300  # increased from 120 – rust/steam can take a while
terminal = "alacritty"
browser = "zen-browser"
power_menu = "eww"
application_launcher = "rofi"
file_manager = "thunar"

failed_packages = []

before_download = ["networkmanager", "git", "base-devel", "archlinux-keyring", "rust", "cargo"]
download_list = [terminal, browser, power_menu, application_launcher, file_manager, "picom", "lib32-libva-mesa-driver", "libva-mesa-driver", "lib32-vulkan-radeon", "vulkan-radeon", "xf86-video-amdgpu", "xorg-server", "xorg-xinit", "mesa", "xf86-input-libinput", "python", "uv", "nano", "rust-analyzer", "windsurf", "steam", "vesktop", "qtile", "pipewire", "pipewire-pulse", "pipewire-alsa", "pipewire-jack", "htop", "fastfetch", "spectacle", "dunst", "feh", "polkit-gnome", "wireplumber", "pavucontrol", "ttf-jetbrains-mono-nerd", "unzip", "python-pywal"]

#<<<-----------------------------------------------------------FUNCTIONS---------------------------------------------------------->>>

# FUNCTION WHICH EXECUTES A COMMAND IN GENERAL
def execute_command(command: str):
    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout


# FUNCTION WHICH INSTALLS A PACKAGE USING PACMAN, YAY, OR FLATPAK
def smart_download_package(package):
    print(f"\nTrying to install package: {package}")
    
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
        print(f"-> {package} successfully installed via pacman.")
        return
    except subprocess.CalledProcessError:
        print(f"Pacman failed for {package}. Trying yay...")

    try:
        execute_command(f"su - tobster -c 'yay -S --needed --noconfirm {package}'")
        print(f"-> {package} successfully installed via yay.")
        return
    except subprocess.CalledProcessError:
        print(f"Yay failed for {package}. Trying Flatpak...")
 
    try:
        search_output = execute_command(f"flatpak search --columns=application {package}")
        if search_output.strip():
            flatpak_id = search_output.split("\n")[0].strip()
            execute_command(f"flatpak install -y flathub {flatpak_id}")
            print(f"-> {package} successfully installed via flatpak ({flatpak_id}).")
            return
    except subprocess.CalledProcessError:
        print(f"Flatpak installation failed for {package}.")
        
    failed_packages.append(package)
    print(f"Error: '{package}' could not be installed anywhere.")


# FUNCTION WHICH INSTALLS A PACKAGE USING PACMAN
def pacman_install(package):
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
    except subprocess.CalledProcessError:
        print(f"Pacman failed for {package}.")
        failed_packages.append(package)


# FUNCTION WHICH INSTALLS A PACKAGE USING YAY
def yay_install(package):
    try:
        execute_command(f"su - tobster -c 'yay -S --needed --noconfirm {package}'")
    except subprocess.CalledProcessError:
        print(f"Yay failed for {package}.")
        failed_packages.append(package)


# FUNCTION WHICH INSTALLS A PACKAGE USING FLATPAK
def flatpak_install(package):
    try:
        execute_command(f"flatpak install -y flathub {package}")
    except subprocess.CalledProcessError:
        print(f"Flatpak failed for {package}.")
        failed_packages.append(package)

# FUNCTION WHICH CLONES A GIT REPOSITORY
def clone_git(url, dest="/tmp/cloned_repo"):
    result = execute_command(f"git clone {url} {dest}")
    return result


# FUNCTION WHICH INSTALLS PACKAGES BEFORE DOWNLOAD
def install_before_packages():
    for package in before_download:
        pacman_install(package)
        
    print("\nBuilding yay manually from AUR...")
    try:
        execute_command("git clone https://aur.archlinux.org/yay.git /tmp/yay")
        execute_command("chown -R tobster:tobster /tmp/yay")
        execute_command("su - tobster -c 'cd /tmp/yay && makepkg -si --noconfirm'")
        print("-> yay successfully installed.")
    except subprocess.CalledProcessError:
        print("Critical error: yay could not be built.")
        failed_packages.append("yay")

# FUNCTION WHICH INSTALLS PACKAGES AFTER DOWNLOAD
def install_packages():
    for package in download_list:
        smart_download_package(package)

# FUNCTION WHICH CLONES THE QTILE CONFIGURATION AND INSTALLS IT
def qtile_config():
    url = "https://github.com/tobiastettenborn193-prog/OS.git"
    clone_git(url, "/tmp/OS_config")

    execute_command("mkdir -p /home/tobster/.config/qtile")
    execute_command("cp /tmp/OS_config/qtile/config.py /home/tobster/.config/qtile/")
    execute_command("chmod +x /home/tobster/.config/qtile/config.py")
    execute_command("mkdir -p /home/tobster/.wallpapers")
    execute_command("chown -R tobster:tobster /home/tobster/.config /home/tobster/.wallpapers")

# FUNCTION WHICH ENABLES THE MULTILIB REPOSITORY, FLATPAK, AND CREATES THE USER
def setup_system_basics():
    try:
        execute_command("sed -i '/\\[multilib\\]/,+1 s/^#//' /etc/pacman.conf")
        execute_command("pacman -Sy")
        execute_command("pacman -S --needed --noconfirm flatpak")
        execute_command("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo")
        print("-> Multilib + Flathub enabled.")
    except subprocess.CalledProcessError:
        print("Failed to enable multilib/flatpak.")

    try:
        execute_command("useradd -m -G wheel -s /bin/bash tobster")
        execute_command("echo 'tobster:password' | chpasswd")
        execute_command("sed -i 's/# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
        print("-> User 'tobster' created and sudo access configured.")
    except subprocess.CalledProcessError:
        print("Failed to create user or setup sudo.")

    try:
        execute_command("systemctl enable NetworkManager")
        print("-> NetworkManager service enabled.")
    except subprocess.CalledProcessError:
        print("Failed to enable NetworkManager.")

# FUNCTION WHICH INSTALLS THE PICOM CONFIGURATION
def picom_config():
    config_dir = "/home/tobster/.config/picom"
    execute_command(f"mkdir -p {config_dir}")
    
    with open(f"{config_dir}/picom.conf", "w") as f:
        f.write(picom_content)
        
    execute_command("chown -R tobster:tobster /home/tobster/.config/picom")
    print("-> Picom configuration installed.")

# FUNCTION WHICH DETECTS THE WIFI INTERFACE AND PATCHES IT INTO THE QTILE CONFIG
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

# FUNCTION WHICH CREATES THE AUTOSTART SCRIPT
def autostart():
    autostart_path = "/home/tobster/.config/qtile/autostart.sh"
    autostart_content = """#!/bin/bash
pipewire &
pipewire-pulse &
wireplumber &
while true; do picom --config ~/.config/picom/picom.conf; sleep 1; done &
"""

    with open(autostart_path, "w") as f:
        f.write(autostart_content)

    execute_command(f"chmod +x {autostart_path}")
    
    try:
        with open("/home/tobster/.xinitrc", "w") as f:
            f.write("exec qtile start\n")
        print("-> .xinitrc configured.")
    except Exception as e:
        print(f"Failed to create .xinitrc: {e}")
        
    execute_command("chown -R tobster:tobster /home/tobster")

#<<<-----------------------------------------------------------MAIN---------------------------------------------------------->>>
def main():
    setup_system_basics()
    install_before_packages()
    install_packages()
    qtile_config()
    detect_wifi_interface()
    picom_config()
    autostart()
    
    print("\n--- Process Finished ---")
    if failed_packages:
        print(f"Failed to install: {', '.join(failed_packages)}")
    else:
        print("Everything successfully installed! Log in as 'tobster' and type 'startx'")

if __name__ == "__main__":
    main()