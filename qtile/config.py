import os
import subprocess
import sys

# <<<-----------------------------------------------------------HYPERPARAMETERS---------------------------------------------------------->>>

picom_content = """
# Backend & Performance
backend = "glx";
vsync = true;
use-damage = true;
glx-no-stencil = true;

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
active-opacity = 1.0;
# inactive-opacity-override wurde entfernt (verursacht Warnungen in neuen Versionen)

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

# [Restliche Config-Strings wie autostart_content, xinitrc_content etc. bleiben exakt gleich]
autostart_content = """#!/bin/bash\npkill picom 2>/dev/null; sleep 0.3\npicom --config ~/.config/picom/picom.conf &\n"""
xinitrc_content = """#!/bin/bash\nif [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then\n    eval $(dbus-launch --sh-syntax --exit-with-session)\nfi\nxhost +local: &> /dev/null\nexec qtile start\n"""
wal_postscript_content = """#!/bin/bash\nsleep 0.3\nqtile cmd-obj -o cmd -f execute_custom_command -a "reload_wal_colors" 2>/dev/null\nif [ $? -ne 0 ]; then\n    qtile-cmd -o cmd -f execute_custom_command -a "reload_wal_colors" 2>/dev/null\nfi\n"""
starship_wal_postscript_content = """#!/bin/bash\nsource ~/.cache/wal/colors.sh\ncat > ~/.config/starship_palette.toml << EOF\n[palettes.wal]\ncolor0 = "$color0"\ncolor1 = "$color1"\ncolor2 = "$color2"\ncolor3 = "$color3"\ncolor4 = "$color4"\ncolor5 = "$color5"\ncolor6 = "$color6"\ncolor7 = "$color7"\nEOF\n"""
cursor_wal_postscript_content = """#!/bin/bash\nsource ~/.cache/wal/colors.sh\nACCENT="$color4"\nBRIGHTNESS=$(python3 -c "\nc='$color4'.lstrip('#')\nr,g,b=int(c[0:2],16),int(c[2:4],16),int(c[4:6],16)\nprint('light' if (r*299+g*587+b*114)/1000 > 128 else 'dark')\n" 2>/dev/null || echo "dark")\nif [ "$BRIGHTNESS" = "light" ]; then\n    CURSOR_THEME="Bibata-Modern-Ice"\nelse\n    CURSOR_THEME="Bibata-Modern-Classic"\nfi\nmkdir -p ~/.config/gtk-3.0\nsed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=$CURSOR_THEME/" ~/.config/gtk-3.0/settings.ini 2>/dev/null\nif ! grep -q "gtk-cursor-theme-name" ~/.config/gtk-3.0/settings.ini 2>/dev/null; then\n    echo "gtk-cursor-theme-name=$CURSOR_THEME" >> ~/.config/gtk-3.0/settings.ini\nfi\nsed -i "s/Xcursor.theme:.*/Xcursor.theme: $CURSOR_THEME/" ~/.Xresources 2>/dev/null\nxsetroot -cursor_name left_ptr 2>/dev/null\n"""
ly_wal_postscript_content = """#!/bin/bash\nsource ~/.cache/wal/colors.sh\nLY_CONFIG="/etc/ly/config.ini"\nif [ -f "$LY_CONFIG" ]; then\n    sudo sed -i "s/^animation = .*/animation = doom/" "$LY_CONFIG" 2>/dev/null\n    sudo sed -i "s/^clear_password = .*/clear_password = true/" "$LY_CONFIG" 2>/dev/null\nfi\necho "-> Ly config updated with wal colors."\n"""
alacritty_wal_postscript_content = """#!/bin/bash\ncat ~/.cache/wal/colors-alacritty.toml > ~/.config/alacritty/colors-live.toml\ntouch ~/.config/alacritty/colors-live.toml\n"""
dunst_wal_postscript_content = """#!/bin/bash\nmkdir -p ~/.config/dunst\nln -sf ~/.cache/wal/dunstrc ~/.config/dunst/dunstrc\nkillall dunst\n"""
starship_content = """\n"$schema" = 'https://starship.rs/config-schema.json'\npalette = "wal"\n[palettes.wal]\ncolor0 = "#1a1a2e"\ncolor1 = "#e06c75"\ncolor2 = "#98c379"\ncolor3 = "#e5c07b"\ncolor4 = "#61afef"\ncolor5 = "#c678dd"\ncolor6 = "#56b6c2"\ncolor7 = "#abb2bf"\nformat = \"\"\"\n[┌─](color7)$directory$git_branch$git_status$git_metrics\n[└─](color7)$python$rust$nodejs$cmd_duration$character\"\"\"\n[directory]\nstyle = "bold color4"\ntruncation_length = 3\ntruncate_to_repo = true\nformat = "[ $path ]($style)[$read_only]($read_only_style) "\n[git_branch]\nsymbol = " "\nstyle = "color5"\nformat = "[on](color7) [$symbol$branch]($style) "\n[git_status]\nstyle = "color1"\nformat = '([$all_status$ahead_behind]($style) )'\nconflicted = "⚡"\nahead = "⇡${count}"\nbehind = "⇣${count}"\ndiverged = "⇕⇡${ahead_count}⇣${behind_count}"\nmodified = "✎${count}"\nuntracked = "?${count}"\nstaged = "+${count}"\ndeleted = "✘${count}"\n[git_metrics]\nadded_style = "color2"\ndeleted_style = "color1"\nformat = '([+$added]($added_style) )([-$deleted]($deleted_style) )'\ndisabled = false\n[python]\nsymbol = " "\nstyle = "color3"\nformat = '[${symbol}${pyenv_prefix}(${version} )(\\($virtualenv\\) )]($style)'\n[rust]\nsymbol = " "\nstyle = "color1"\nformat = '[$symbol($version )]($style)'\n[nodejs]\nsymbol = " "\nstyle = "color2"\nformat = '[$symbol($version )]($style)'\n[cmd_duration]\nmin_time = 2_000\nstyle = "color3"\nformat = "[⏱ $duration]($style) "\n[character]\nsuccess_symbol = "[❯](color2)"\nerror_symbol = "[❯](color1)"\n"""
alacritty_content = """[general]\nimport = ["~/.config/alacritty/colors-live.toml"]\n[shell]\nprogram = "/bin/zsh"\nargs = ["--login"]\n[window]\npadding.x = 12\npadding.y = 10\ndecorations = "none"\nopacity = 0.95\nblur = true\n[font]\nnormal = { family = "JetBrainsMono Nerd Font", style = "Regular" }\nbold   = { family = "JetBrainsMono Nerd Font", style = "Bold" }\nitalic = { family = "JetBrainsMono Nerd Font", style = "Italic" }\nsize   = 12.0\n[cursor]\nstyle = { shape = "Block", blinking = "On" }\nblink_interval = 750\n[scrolling]\nhistory = 10000\n[selection]\nsave_to_clipboard = true\n"""
alacritty_wal_template = """# Generated by pywal — do not edit manually\n[colors.primary]\nbackground = "{background}"\nforeground = "{foreground}"\n[colors.normal]\nblack   = "{color0}"\nred     = "{color1}"\ngreen   = "{color2}"\nyellow  = "{color3}"\nblue    = "{color4}"\nmagenta = "{color5}"\ncyan    = "{color6}"\nwhite   = "{color7}"\n[colors.bright]\nblack   = "{color8}"\nred     = "{color9}"\ngreen   = "{color10}"\nyellow  = "{color11}"\nblue    = "{color12}"\nmagenta = "{color13}"\ncyan    = "{color14}"\nwhite   = "{color15}"\n"""
rofi_content = """configuration {\n    modi: "drun,run,window";\n    font: "JetBrainsMono Nerd Font 12";\n    show-icons: true;\n    icon-theme: "Papirus-Dark";\n    display-drun: " Apps";\n    display-run: " Run";\n    display-window: " Windows";\n    drun-display-format: "{name}";\n    hover-select: false;\n    me-select-entry: "";\n    me-accept-entry: "MousePrimary";\n}\n@theme "/dev/null"\n* {\n    bg:      #1a1a2e99;\n    bg-alt:  #16213e99;\n    fg:      #abb2bf;\n    accent:  #61afef;\n    urgent:  #e06c75;\n    background-color:  @bg;\n    text-color:        @fg;\n    border-color:      @accent;\n}\nwindow {\n    width: 500px;\n    border: 1px;\n    border-radius: 12px;\n    padding: 8px;\n    background-color: @bg;\n}\nmainbox {\n    padding: 8px;\n    background-color: transparent;\n}\ninputbar {\n    padding: 8px 12px;\n    margin: 0 0 8px 0;\n    border-radius: 8px;\n    background-color: @bg-alt;\n    children: [prompt, entry];\n}\nprompt {\n    padding: 0 8px 0 0;\n    text-color: @accent;\n}\nentry {\n    text-color: @fg;\n    placeholder: "Search...";\n    placeholder-color: #555;\n}\nlistview {\n    lines: 8;\n    scrollbar: false;\n    background-color: transparent;\n}\nelement {\n    padding: 8px 12px;\n    border-radius: 8px;\n    background-color: transparent;\n    text-color: @fg;\n}\nelement selected {\n    background-color: @bg-alt;\n    text-color: @accent;\n}\nelement-icon {\n    size: 20px;\n    padding: 0 8px 0 0;\n}\n"""
rofi_wal_postscript_content = """#!/bin/bash\nsource ~/.cache/wal/colors.sh\nROFI_CONFIG="$HOME/.config/rofi/config.rasi"\nif [ -f "$ROFI_CONFIG" ]; then\n    sed -i "s/bg:      #[0-9a-fA-F]*/bg:      ${color0}/" "$ROFI_CONFIG"\n    sed -i "s/bg-alt:  #[0-9a-fA-F]*/bg-alt:  ${color1}/" "$ROFI_CONFIG"\n    sed -i "s/fg:      #[0-9a-fA-F]*/fg:      ${color7}/" "$ROFI_CONFIG"\n    sed -i "s/accent:  #[0-9a-fA-F]*/accent:  ${color4}/" "$ROFI_CONFIG"\n    sed -i "s/urgent:  #[0-9a-fA-F]*/urgent:  ${color1}/" "$ROFI_CONFIG"\n    echo "-> Rofi colors updated."\nfi\n"""
gtk_wal_postscript_content = """#!/bin/bash\nsource ~/.cache/wal/colors.sh\nGTK_CSS="$HOME/.config/gtk-3.0/gtk.css"\nGTK_SETTINGS="$HOME/.config/gtk-3.0/settings.ini"\nmkdir -p "$HOME/.config/gtk-3.0"\ncat > "$GTK_CSS" << EOF\n/* Auto-generated by gtk_wal_reload.sh — do not edit manually */\n@define-color accent_color ${color4};\n@define-color accent_bg_color ${color4};\n@define-color accent_fg_color ${color0};\n@define-color window_bg_color ${color0};\n@define-color window_fg_color ${color7};\n@define-color view_bg_color ${color1};\n@define-color view_fg_color ${color7};\n@define-color headerbar_bg_color ${color0};\n@define-color headerbar_fg_color ${color7};\n@define-color headerbar_border_color ${color8};\n@define-color sidebar_bg_color ${color1};\n@define-color sidebar_fg_color ${color7};\n@define-color sidebar_shade_color alpha(black, 0.15);\n@define-color card_bg_color ${color1};\n@define-color card_fg_color ${color7};\n@define-color popover_bg_color ${color1};\n@define-color popover_fg_color ${color7};\n@define-color dialog_bg_color ${color0};\n@define-color dialog_fg_color ${color7};\n@define-color warning_color ${color3};\n@define-color error_color ${color1};\n@define-color success_color ${color2};\nselection {\n  background-color: ${color4};\n  color: ${color0};\n}\nscrollbar slider {\n  background-color: ${color8};\n  border-radius: 6px;\n  min-width: 6px;\n  min-height: 6px;\n}\nscrollbar slider:hover {\n  background-color: ${color4};\n}\n.nautilus-window .sidebar,\n.nemo-window .sidebar {\n  background-color: ${color1};\n  color: ${color7};\n}\nrow:selected,\nrow:selected label {\n  background-color: ${color4};\n  color: ${color0};\n}\nEOF\necho "-> gtk.css updated with wal colors."\nif [ -f "$GTK_SETTINGS" ]; then\n    sed -i "s/gtk-theme-name=.*/gtk-theme-name=Adwaita-dark/" "$GTK_SETTINGS"\nfi\nGTK4_CSS="$HOME/.config/gtk-4.0/gtk.css"\nif [ -d "$HOME/.config/gtk-4.0" ]; then\n    cp "$GTK_CSS" "$GTK4_CSS"\n    echo "-> gtk4.css updated."\nfi\nif command -v gsettings &>/dev/null; then\n    gsettings set org.gnome.desktop.interface gtk-theme "Adwaita" 2>/dev/null\n    sleep 0.1\n    gsettings set org.gnome.desktop.interface gtk-theme "Adwaita-dark" 2>/dev/null\n    echo "-> GTK theme reloaded via gsettings."\nfi\necho "-> GTK/Nemo pywal colors applied."\n"""
gtk_settings_content = """[Settings]\ngtk-theme-name=Adwaita-dark\ngtk-icon-theme-name=Papirus-Dark\ngtk-font-name=JetBrainsMono Nerd Font 10\ngtk-cursor-theme-name=Bibata-Modern-Classic\ngtk-cursor-theme-size=24\ngtk-toolbar-style=GTK_TOOLBAR_ICONS\ngtk-button-images=0\ngtk-menu-images=1\ngtk-enable-event-sounds=0\ngtk-enable-input-feedback-sounds=0\ngtk-xft-antialias=1\ngtk-xft-hinting=1\ngtk-xft-hintstyle=hintslight\ngtk-xft-rgba=rgb\n"""
xresources_content = """Xcursor.theme: Bibata-Modern-Classic\nXcursor.size: 24\n! pywal colors — auto-generated, do not edit below this line\n"""
ly_config_content = """[config]\ntty = 2\nanimation = doom\nhide_borders = true\nvi_mode = false\nclear_password = true\nblank_box = true\nshutdown_cmd = /sbin/shutdown -h now\nrestart_cmd = /sbin/shutdown -r now\nterm_reset_cmd = tput reset\nnumlock = true\n"""

timeout = 10000
terminal = "alacritty"
browser = "zen-browser"
power_menu = "eww"
application_launcher = "rofi"
file_manager = "nemo"

failed_packages = []

before_download = [
    "networkmanager",
    "git",
    "base-devel",
    "archlinux-keyring",
    "rust",
    "cargo",
    "go",
    "reflector",
    "pciutils", # WICHTIG: Wird für lspci (GPU detection) gebraucht
]

download_list = [
    "zsh",
    "starship",
    terminal,
    application_launcher,
    file_manager,
    "nemo-fileroller",
    "picom",
    "xorg-server",
    "xorg-xinit",
    "xorg-xauth",
    "xf86-input-libinput",
    "python",
    "python-pip",
    "python-dotenv", # Wichtig für dein neues Setup
    "uv",
    "nano",
    "rust-analyzer",
    "steam",
    "vesktop",
    "qtile",
    "pipewire",
    "pipewire-pulse",
    "pipewire-alsa",
    "pipewire-jack",
    "htop",
    "fastfetch",
    "spectacle",
    "dunst",
    "libnotify",
    "feh",
    "polkit-gnome",
    "wireplumber",
    "pavucontrol",
    "ttf-jetbrains-mono-nerd",
    "unzip",
    "python-pywal",
    "bluez",
    "bluez-utils",
    "papirus-icon-theme",
    "ly",
    "wireshark-qt",
    "jdk17-openjdk",
    "prismlauncher",
    "librewolf",
    "olama",
    "tailscale",
    "obsidian",
    "brightnessctl",
    "btop",
    "fzf",
    "yazi",
    "playerctl",
    "python-pulsectl-asyncio",
    "esptool",
]

aur_packages = [
    "zen-browser-bin",
    "windsurf-bin",
    "bibata-cursor-theme-bin",
    "localsend-bin",
    "oh-my-zsh-git",
    "zellij",
    "mullvad-vpn-bin",
]

# <<<-----------------------------------------------------------FUNCTIONS---------------------------------------------------------->>>

TOBSTER_ENV = {
    "HOME": "/home/tobster",
    "USER": "tobster",
    "LOGNAME": "tobster",
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/tobster/.local/bin:/home/tobster/go/bin",
    "TERM": "xterm",
    "GOPATH": "/home/tobster/go",
    "GOCACHE": "/home/tobster/.cache/go",
    "GOPROXY": "https://proxy.golang.org,direct",
    "XDG_CACHE_HOME": "/home/tobster/.cache",
    "XDG_RUNTIME_DIR": "/run/user/1000",
}


def execute_command(command: str, as_user: bool = False):
    if as_user:
        result = subprocess.run(
            ["sudo", "-u", "tobster", "bash", "-c", f"HOME=/home/tobster {command}"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, command, result.stdout, result.stderr
            )
        return result.stdout
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout}s: {command}")
        raise
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, e.stderr)

def update_mirrors():
    print("\nUpdating Pacman Mirrors...")
    try:
        execute_command("pacman -S --needed --noconfirm reflector")
        execute_command("reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist")
        execute_command("pacman -Syy")
        print("-> Mirrors successfully updated.")
    except Exception as e:
        print(f"Failed to update mirrors: {e}")

def install_yay():
    print("\nBuilding yay-bin from AUR...")
    BUILD_DIR = "/home/tobster/.cache/yay-build"
    try:
        execute_command("pacman -S --needed --noconfirm base-devel git")
        execute_command(f"rm -rf {BUILD_DIR}")
        execute_command(f"mkdir -p {BUILD_DIR}")
        execute_command(f"chown -R tobster:tobster {BUILD_DIR}")
        build_cmd = (
            "export HOME=/home/tobster && "
            "export USER=tobster && "
            f"cd {BUILD_DIR} && "
            "git clone https://aur.archlinux.org/yay-bin.git . && "
            "makepkg -si --noconfirm 2>&1"
        )
        result = subprocess.run(
            ["sudo", "-u", "tobster", "bash", "-c", build_cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, "makepkg yay-bin")
        print("-> yay successfully installed.")
    except Exception as e:
        print(f"Critical: yay could not be built: {e}")
        failed_packages.append("yay")

def yay_install(package: str):
    print(f"\n[yay] Installing: {package}")
    try:
        result = subprocess.run(
            ["sudo", "-u", "tobster", "yay", "-S", "--needed", "--noconfirm", "--answerclean", "None", "--answerdiff", "None", package],
            capture_output=True, text=True, timeout=timeout, env=TOBSTER_ENV
        )
        if result.returncode != 0:
            failed_packages.append(package)
        else:
            print(f"-> {package} installed via yay.")
    except subprocess.TimeoutExpired:
        failed_packages.append(package)

def pacman_install(package: str):
    print(f"\n[pacman] Installing: {package}")
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
        print(f"-> {package} installed via pacman.")
    except Exception:
        failed_packages.append(package)

def smart_download_package(package: str):
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
        print(f"-> {package} via pacman.")
        return
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["sudo", "-u", "tobster", "yay", "-S", "--needed", "--noconfirm", "--answerclean", "None", "--answerdiff", "None", package],
            capture_output=True, text=True, timeout=timeout, env=TOBSTER_ENV
        )
        if result.returncode == 0:
            print(f"-> {package} via yay.")
            return
    except Exception:
        pass
    failed_packages.append(package)

def clone_git(url: str, dest: str = "/tmp/cloned_repo"):
    return execute_command(f"git clone {url} {dest}")

def install_before_packages():
    for package in before_download:
        pacman_install(package)

def install_packages():
    for package in download_list:
        smart_download_package(package)

def install_aur_packages():
    print("\n--- Installing AUR-only packages ---")
    for package in aur_packages:
        yay_install(package)

def detect_and_install_gpu_drivers():
    print("\n--- Detecting GPU and installing specific drivers ---")
    try:
        # lspci fragt die Hardware ab
        lspci_output = execute_command("lspci -k | grep -E '(VGA|3D)'").lower()
        gpu_packages = ["mesa", "lib32-mesa", "vulkan-mesa-layers", "lib32-vulkan-mesa-layers"]

        if "nvidia" in lspci_output:
            print("-> NVIDIA GPU detected. Fetching proprietary drivers...")
            gpu_packages.extend(["nvidia-dkms", "nvidia-utils", "lib32-nvidia-utils", "nvidia-settings"])
        elif "amd" in lspci_output or "radeon" in lspci_output:
            print("-> AMD GPU detected. Fetching open-source drivers...")
            gpu_packages.extend(["xf86-video-amdgpu", "vulkan-radeon", "lib32-vulkan-radeon", "libva-mesa-driver", "lib32-libva-mesa-driver"])
        elif "intel" in lspci_output:
            print("-> Intel GPU detected. Fetching intel specific drivers...")
            gpu_packages.extend(["xf86-video-intel", "vulkan-intel", "lib32-vulkan-intel"])
        else:
            print("-> Unknown GPU. Sticking to base mesa drivers.")

        for pkg in gpu_packages:
            smart_download_package(pkg)

    except Exception as e:
        print(f"Failed to auto-detect/install GPU drivers: {e}")

def install_oh_my_zsh():
    print("\nInstalling oh-my-zsh...")
    try:
        result = subprocess.run(
            ["sudo", "-u", "tobster", "bash", "-c", 'HOME=/home/tobster RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'],
            capture_output=True, text=True, timeout=timeout, env=TOBSTER_ENV
        )
        if result.returncode == 0:
            print("-> oh-my-zsh installed.")
            execute_command("git clone https://github.com/zsh-users/zsh-autosuggestions /home/tobster/.oh-my-zsh/custom/plugins/zsh-autosuggestions", as_user=True)
            execute_command("git clone https://github.com/zsh-users/zsh-syntax-highlighting.git /home/tobster/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting", as_user=True)
    except Exception:
        failed_packages.append("oh-my-zsh")

def qtile_config():
    print("\nCloning and applying Qtile config (Recursive)...")
    url = "https://github.com/tobiastettenborn193-prog/OS.git"
    clone_git(url, "/tmp/OS_config")

    # Der wichtigste Fix: Ordner komplett und rekursiv rüberziehen
    execute_command("mkdir -p /home/tobster/.config/qtile")
    execute_command("cp -rf /tmp/OS_config/qtile/* /home/tobster/.config/qtile/")

    # Permissions für Scripte und Ordner anpassen
    execute_command("chmod +x /home/tobster/.config/qtile/config.py")
    try:
        execute_command("chmod -R +x /home/tobster/.config/qtile/scripts/")
    except Exception:
        pass

    execute_command("mkdir -p /home/tobster/.wallpapers")
    execute_command("chown -R tobster:tobster /home/tobster/.config/qtile /home/tobster/.wallpapers")

def setup_zsh():
    print("\nConfiguring ZSH as default shell...")
    zshrc_src = "/tmp/OS_config/zsh/zsh.zshrc"
    zshrc_dst = "/home/tobster/.zshrc"
    try:
        execute_command("grep -qxF '/bin/zsh' /etc/shells || echo '/bin/zsh' >> /etc/shells")

        # Sicherer Weg, die Shell zu ändern, ohne /etc/passwd zu crashen
        execute_command("usermod -s /bin/zsh tobster")

        # ZSHRC kopieren (nur wenn sie im Repo existiert, sonst greift der Oh-My-Zsh Standard)
        try:
            execute_command(f"cp {zshrc_src} {zshrc_dst}")
            execute_command(f"chown tobster:tobster {zshrc_dst}")
            print("-> Custom .zshrc applied.")
        except Exception:
            print("-> Note: No custom zshrc found in repo, using Oh-My-Zsh defaults.")

    except Exception as e:
        print(f"Failed to setup ZSH: {e}")

def setup_system_basics():
    try:
        execute_command("sed -i '/\\[multilib\\]/,+1 s/^#//' /etc/pacman.conf")
        execute_command("pacman -Syy")
        execute_command("pacman -S --needed --noconfirm flatpak")
        execute_command("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo")
    except Exception:
        pass

    try:
        execute_command("useradd -m -G wheel -s /bin/zsh tobster")
        execute_command("echo 'tobster:password' | chpasswd")
        execute_command("sed -i 's/# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")
    except Exception:
        execute_command("sed -i 's/# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")
        execute_command("sed -i 's/%wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")

    try:
        execute_command("systemctl enable NetworkManager")
    except Exception:
        pass
    setup_locale()

def setup_locale():
    try:
        execute_command("sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen")
        execute_command("sed -i 's/#de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen")
        execute_command("locale-gen")
        with open("/etc/locale.conf", "w") as f:
            f.write("LANG=en_US.UTF-8\nLC_TIME=en_US.UTF-8\nLC_MESSAGES=en_US.UTF-8\n")
        execute_command("localectl set-keymap de")
        execute_command("localectl set-x11-keymap de")
        execute_command("mkdir -p /home/tobster/.config/locale")
        with open("/home/tobster/.config/locale.conf", "w") as f:
            f.write("LANG=en_US.UTF-8\n")
        execute_command("chown tobster:tobster /home/tobster/.config/locale.conf")
    except Exception:
        pass

def picom_config():
    config_dir = "/home/tobster/.config/picom"
    execute_command(f"mkdir -p {config_dir}")
    with open(f"{config_dir}/picom.conf", "w") as f:
        f.write(picom_content)
    execute_command("chown -R tobster:tobster /home/tobster/.config/picom")

# Die restlichen kleinen Helper-Funktionen (Firewall, Opsec, Alacritty, Ly, Starship etc.) bleiben unverändert,
# ich habe sie der Übersicht halber aus dem Snippet gekürzt.
# Füge einfach deine originalen setup_firewall(), setup_opsec(), setup_cursor() etc. hier exakt wie vorher ein!

# [ ... PLATZHALTER FÜR DEINE RESTLICHEN FUNKTIONEN (setup_firewall, setup_alacritty etc.) ... ]

def main():
    try:
        update_mirrors()
        setup_system_basics()
        # [ setup_opsec() & setup_firewall() hier aufrufen ]
        install_before_packages()
        install_yay()

        # GPU Check VOR der normalen Paket-Schleife ausführen
        detect_and_install_gpu_drivers()

        install_packages()
        install_aur_packages()
        # [ install_eww() hier aufrufen ]
        install_oh_my_zsh()
        setup_zsh() # Nach Oh-My-Zsh ausführen!

        qtile_config() # Nutzt jetzt den rekursiven Fix für Ordner

        # [ restliche config Funktionen wie picom_config() hier aufrufen ]
        picom_config()

    finally:
        print("\nRestoring sudo security settings...")
        execute_command("sed -i 's/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
        print("-> Sudo password requirement for 'tobster' re-enabled.")

    print("\n--- Process Finished ---")
    if failed_packages:
        print(f"Failed to install: {', '.join(failed_packages)}")
    else:
        print("Everything installed! Reboot — Ly will greet you.")

if __name__ == "__main__":
    main()
