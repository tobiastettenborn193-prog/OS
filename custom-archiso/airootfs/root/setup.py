import os
import subprocess
import sys

# <<<-----------------------------------------------------------HYPERPARAMETERS---------------------------------------------------------->>>

picom_content = """
# Backend & Performance
backend = "glx";
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

autostart_content = """#!/bin/bash
pkill picom 2>/dev/null; sleep 0.3
picom --config ~/.config/picom/picom.conf &
"""

xinitrc_content = """#!/bin/bash
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax --exit-with-session)
fi
xhost +local: &> /dev/null
exec qtile start
"""

wal_postscript_content = """#!/bin/bash
sleep 0.3
qtile cmd-obj -o cmd -f execute_custom_command -a "reload_wal_colors" 2>/dev/null
if [ $? -ne 0 ]; then
    qtile-cmd -o cmd -f execute_custom_command -a "reload_wal_colors" 2>/dev/null
fi
"""

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

cursor_wal_postscript_content = """#!/bin/bash
source ~/.cache/wal/colors.sh

ACCENT="$color4"
BRIGHTNESS=$(python3 -c "
c='$color4'.lstrip('#')
r,g,b=int(c[0:2],16),int(c[2:4],16),int(c[4:6],16)
print('light' if (r*299+g*587+b*114)/1000 > 128 else 'dark')
" 2>/dev/null || echo "dark")

if [ "$BRIGHTNESS" = "light" ]; then
    CURSOR_THEME="Bibata-Modern-Ice"
else
    CURSOR_THEME="Bibata-Modern-Classic"
fi

mkdir -p ~/.config/gtk-3.0
sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=$CURSOR_THEME/" ~/.config/gtk-3.0/settings.ini 2>/dev/null
if ! grep -q "gtk-cursor-theme-name" ~/.config/gtk-3.0/settings.ini 2>/dev/null; then
    echo "gtk-cursor-theme-name=$CURSOR_THEME" >> ~/.config/gtk-3.0/settings.ini
fi

sed -i "s/Xcursor.theme:.*/Xcursor.theme: $CURSOR_THEME/" ~/.Xresources 2>/dev/null
xsetroot -cursor_name left_ptr 2>/dev/null
"""

ly_wal_postscript_content = """#!/bin/bash
source ~/.cache/wal/colors.sh

LY_CONFIG="/etc/ly/config.ini"
if [ -f "$LY_CONFIG" ]; then
    sudo sed -i "s/^animation = .*/animation = doom/" "$LY_CONFIG" 2>/dev/null
    sudo sed -i "s/^clear_password = .*/clear_password = true/" "$LY_CONFIG" 2>/dev/null
fi

echo "-> Ly config updated with wal colors."
"""

alacritty_wal_postscript_content = """#!/bin/bash
cat ~/.cache/wal/colors-alacritty.toml > ~/.config/alacritty/colors-live.toml
touch ~/.config/alacritty/colors-live.toml
"""

starship_content = """
"$schema" = 'https://starship.rs/config-schema.json'

palette = "wal"

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
format = '[${symbol}${pyenv_prefix}(${version} )(\\($virtualenv\\) )]($style)'

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

alacritty_content = """import = ["~/.config/alacritty/colors-live.toml"]

[shell]
program = "/bin/zsh"
args = ["--login"]

[window]
padding.x = 12
padding.y = 10
decorations = "none"
opacity = 0.95
blur = true

[font]
normal = { family = "JetBrainsMono Nerd Font", style = "Regular" }
bold   = { family = "JetBrainsMono Nerd Font", style = "Bold" }
italic = { family = "JetBrainsMono Nerd Font", style = "Italic" }
size   = 12.0

[cursor]
style = { shape = "Block", blinking = "On" }
blink_interval = 750

[scrolling]
history = 10000

[selection]
save_to_clipboard = true
"""

alacritty_wal_template = """# Generated by pywal — do not edit manually
[colors.primary]
background = "{background}"
foreground = "{foreground}"

[colors.normal]
black   = "{color0}"
red     = "{color1}"
green   = "{color2}"
yellow  = "{color3}"
blue    = "{color4}"
magenta = "{color5}"
cyan    = "{color6}"
white   = "{color7}"

[colors.bright]
black   = "{color8}"
red     = "{color9}"
green   = "{color10}"
yellow  = "{color11}"
blue    = "{color12}"
magenta = "{color13}"
cyan    = "{color14}"
white   = "{color15}"
"""

rofi_content = """configuration {
    modi: "drun,run,window";
    font: "JetBrainsMono Nerd Font 12";
    show-icons: true;
    icon-theme: "Papirus-Dark";
    display-drun: " Apps";
    display-run: " Run";
    display-window: " Windows";
    drun-display-format: "{name}";
    hover-select: false;
    me-select-entry: "";
    me-accept-entry: "MousePrimary";
}

@theme "/dev/null"

* {
    bg:      #1a1a2e99;
    bg-alt:  #16213e99;
    fg:      #abb2bf;
    accent:  #61afef;
    urgent:  #e06c75;

    background-color:  @bg;
    text-color:        @fg;
    border-color:      @accent;
}

window {
    width: 500px;
    border: 1px;
    border-radius: 12px;
    padding: 8px;
    background-color: @bg;
}

mainbox {
    padding: 8px;
    background-color: transparent;
}

inputbar {
    padding: 8px 12px;
    margin: 0 0 8px 0;
    border-radius: 8px;
    background-color: @bg-alt;
    children: [prompt, entry];
}

prompt {
    padding: 0 8px 0 0;
    text-color: @accent;
}

entry {
    text-color: @fg;
    placeholder: "Search...";
    placeholder-color: #555;
}

listview {
    lines: 8;
    scrollbar: false;
    background-color: transparent;
}

element {
    padding: 8px 12px;
    border-radius: 8px;
    background-color: transparent;
    text-color: @fg;
}

element selected {
    background-color: @bg-alt;
    text-color: @accent;
}

element-icon {
    size: 20px;
    padding: 0 8px 0 0;
}
"""

rofi_wal_postscript_content = """#!/bin/bash
source ~/.cache/wal/colors.sh

ROFI_CONFIG="$HOME/.config/rofi/config.rasi"
if [ -f "$ROFI_CONFIG" ]; then
    sed -i "s/bg:      #[0-9a-fA-F]*/bg:      ${color0}/" "$ROFI_CONFIG"
    sed -i "s/bg-alt:  #[0-9a-fA-F]*/bg-alt:  ${color1}/" "$ROFI_CONFIG"
    sed -i "s/fg:      #[0-9a-fA-F]*/fg:      ${color7}/" "$ROFI_CONFIG"
    sed -i "s/accent:  #[0-9a-fA-F]*/accent:  ${color4}/" "$ROFI_CONFIG"
    sed -i "s/urgent:  #[0-9a-fA-F]*/urgent:  ${color1}/" "$ROFI_CONFIG"
    echo "-> Rofi colors updated."
fi
"""

gtk_wal_postscript_content = """#!/bin/bash
source ~/.cache/wal/colors.sh

GTK_CSS="$HOME/.config/gtk-3.0/gtk.css"
GTK_SETTINGS="$HOME/.config/gtk-3.0/settings.ini"

mkdir -p "$HOME/.config/gtk-3.0"

cat > "$GTK_CSS" << EOF
/* Auto-generated by gtk_wal_reload.sh — do not edit manually */

@define-color accent_color ${color4};
@define-color accent_bg_color ${color4};
@define-color accent_fg_color ${color0};

@define-color window_bg_color ${color0};
@define-color window_fg_color ${color7};

@define-color view_bg_color ${color1};
@define-color view_fg_color ${color7};

@define-color headerbar_bg_color ${color0};
@define-color headerbar_fg_color ${color7};
@define-color headerbar_border_color ${color8};

@define-color sidebar_bg_color ${color1};
@define-color sidebar_fg_color ${color7};
@define-color sidebar_shade_color alpha(black, 0.15);

@define-color card_bg_color ${color1};
@define-color card_fg_color ${color7};

@define-color popover_bg_color ${color1};
@define-color popover_fg_color ${color7};

@define-color dialog_bg_color ${color0};
@define-color dialog_fg_color ${color7};

@define-color warning_color ${color3};
@define-color error_color ${color1};
@define-color success_color ${color2};

selection {
  background-color: ${color4};
  color: ${color0};
}

scrollbar slider {
  background-color: ${color8};
  border-radius: 6px;
  min-width: 6px;
  min-height: 6px;
}

scrollbar slider:hover {
  background-color: ${color4};
}

.nautilus-window .sidebar,
.nemo-window .sidebar {
  background-color: ${color1};
  color: ${color7};
}

row:selected,
row:selected label {
  background-color: ${color4};
  color: ${color0};
}
EOF

echo "-> gtk.css updated with wal colors."

if [ -f "$GTK_SETTINGS" ]; then
    sed -i "s/gtk-theme-name=.*/gtk-theme-name=Adwaita-dark/" "$GTK_SETTINGS"
fi

GTK4_CSS="$HOME/.config/gtk-4.0/gtk.css"
if [ -d "$HOME/.config/gtk-4.0" ]; then
    cp "$GTK_CSS" "$GTK4_CSS"
    echo "-> gtk4.css updated."
fi

if command -v gsettings &>/dev/null; then
    gsettings set org.gnome.desktop.interface gtk-theme "Adwaita" 2>/dev/null
    sleep 0.1
    gsettings set org.gnome.desktop.interface gtk-theme "Adwaita-dark" 2>/dev/null
    echo "-> GTK theme reloaded via gsettings."
fi

echo "-> GTK/Nemo pywal colors applied."
"""

gtk_settings_content = """[Settings]
gtk-theme-name=Adwaita-dark
gtk-icon-theme-name=Papirus-Dark
gtk-font-name=JetBrainsMono Nerd Font 10
gtk-cursor-theme-name=Bibata-Modern-Classic
gtk-cursor-theme-size=24
gtk-toolbar-style=GTK_TOOLBAR_ICONS
gtk-button-images=0
gtk-menu-images=1
gtk-enable-event-sounds=0
gtk-enable-input-feedback-sounds=0
gtk-xft-antialias=1
gtk-xft-hinting=1
gtk-xft-hintstyle=hintslight
gtk-xft-rgba=rgb
"""

xresources_content = """Xcursor.theme: Bibata-Modern-Classic
Xcursor.size: 24

! pywal colors — auto-generated, do not edit below this line
"""

ly_config_content = """[config]
tty = 2
animation = doom
hide_borders = true
vi_mode = false
clear_password = true
blank_box = true
shutdown_cmd = /sbin/shutdown -h now
restart_cmd = /sbin/shutdown -r now
term_reset_cmd = tput reset
numlock = true
"""

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
]


download_list = [
    "zsh",
    "starship",
    terminal,
    application_launcher,
    file_manager,
    "nemo-fileroller",  # Verschoben aus AUR
    "picom",
    "lib32-libva-mesa-driver",
    "libva-mesa-driver",
    "lib32-vulkan-radeon",
    "vulkan-radeon",
    "xf86-video-amdgpu",
    "xorg-server",
    "xorg-xinit",
    "xorg-xauth",
    "mesa",
    "xf86-input-libinput",
    "python",
    "python-pip",
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
]

aur_packages = [
    "zen-browser-bin",
    "windsurf-bin",
    "bibata-cursor-theme-bin",
    "localsend-bin",
    "oh-my-zsh-git",
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


def install_yay():
    print("\nBuilding yay from AUR...")

    BUILD_DIR = "/home/tobster/.cache/yay-build"

    try:
        execute_command("pacman -S --needed --noconfirm base-devel git go cmake")

        execute_command(f"rm -rf {BUILD_DIR}")
        execute_command(f"mkdir -p {BUILD_DIR}")
        execute_command(f"chown -R tobster:tobster {BUILD_DIR}")

        execute_command("mkdir -p /home/tobster/go /home/tobster/.cache/go")
        execute_command(
            "chown -R tobster:tobster /home/tobster/go /home/tobster/.cache/go"
        )

        build_cmd = (
            "export HOME=/home/tobster && "
            "export LOGNAME=tobster && "
            "export GOPATH=/home/tobster/go && "
            "export GOCACHE=/home/tobster/.cache/go && "
            "export GOPROXY=https://proxy.golang.org,direct && "
            "export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/go/bin:/home/tobster/go/bin && "
            f"cd {BUILD_DIR} && "
            "git clone https://aur.archlinux.org/yay.git . && "
            "makepkg -si --syncdeps --noconfirm --needed --skippgpcheck 2>&1"
        )

        result = subprocess.run(
            ["sudo", "-u", "tobster", "bash", "-c", build_cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=TOBSTER_ENV,
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, "makepkg yay")

        print("-> yay successfully installed.")

    except Exception as e:
        print(f"Critical: yay could not be built: {e}")
        failed_packages.append("yay")


def yay_install(package: str):
    print(f"\n[yay] Installing: {package}")
    try:
        result = subprocess.run(
            [
                "sudo",
                "-u",
                "tobster",
                "yay",
                "-S",
                "--needed",
                "--noconfirm",
                "--answerclean",
                "None",
                "--answerdiff",
                "None",
                package,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            print(f"[!] yay failed for {package} (exit {result.returncode})")
            print(f"Error Log:\n{result.stderr}\n{result.stdout[-1000:]}")
            failed_packages.append(package)
        else:
            print(f"-> {package} installed via yay.")
    except subprocess.TimeoutExpired:
        print(f"yay timed out for {package} (>{timeout}s)")
        failed_packages.append(package)


def pacman_install(package: str):
    print(f"\n[pacman] Installing: {package}")
    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
        print(f"-> {package} installed via pacman.")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"pacman failed for {package}: {getattr(e, 'stderr', '')}")
        failed_packages.append(package)


def smart_download_package(package: str):
    print(f"\nInstalling: {package}")

    try:
        execute_command(f"pacman -S --needed --noconfirm {package}")
        print(f"-> {package} via pacman.")
        return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    try:
        result = subprocess.run(
            [
                "sudo",
                "-u",
                "tobster",
                "yay",
                "-S",
                "--needed",
                "--noconfirm",
                "--answerclean",
                "None",
                "--answerdiff",
                "None",
                package,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=TOBSTER_ENV,
        )
        if result.returncode == 0:
            print(f"-> {package} via yay.")
            return
    except subprocess.TimeoutExpired:
        pass

    try:
        search = execute_command(f"flatpak search --columns=application {package}")
        if search.strip():
            flatpak_id = search.split("\n")[0].strip()
            execute_command(f"flatpak install -y flathub {flatpak_id}")
            print(f"-> {package} via flatpak ({flatpak_id}).")
            return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    failed_packages.append(package)
    print(f"Error: '{package}' could not be installed.")


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


def install_eww():
    print("\n--- Installing eww-git ---")
    # eww-git baut über Cargo und erfordert ggf. zusätzliche Schlüssel.
    # Durch den separierten Call wird die Standardinstallation nicht blockiert.
    yay_install("eww-git")


def install_oh_my_zsh():
    print("\nInstalling oh-my-zsh...")
    try:
        result = subprocess.run(
            [
                "sudo",
                "-u",
                "tobster",
                "bash",
                "-c",
                'HOME=/home/tobster RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"',
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            print(f"oh-my-zsh stderr: {result.stderr}")
            failed_packages.append("oh-my-zsh")
        else:
            print("-> oh-my-zsh installed.")

            print(
                "-> Installing zsh plugins (autosuggestions & syntax-highlighting)..."
            )
            execute_command(
                "git clone https://github.com/zsh-users/zsh-autosuggestions /home/tobster/.oh-my-zsh/custom/plugins/zsh-autosuggestions",
                as_user=True,
            )
            execute_command(
                "git clone https://github.com/zsh-users/zsh-syntax-highlighting.git /home/tobster/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting",
                as_user=True,
            )

    except subprocess.TimeoutExpired:
        print("oh-my-zsh install timed out.")
        failed_packages.append("oh-my-zsh")


def qtile_config():
    url = "https://github.com/tobiastettenborn193-prog/OS.git"
    clone_git(url, "/tmp/OS_config")
    execute_command("mkdir -p /home/tobster/.config/qtile")
    execute_command("cp /tmp/OS_config/qtile/config.py /home/tobster/.config/qtile/")
    execute_command("chmod +x /home/tobster/.config/qtile/config.py")
    execute_command("mkdir -p /home/tobster/.wallpapers")
    execute_command(
        "chown -R tobster:tobster /home/tobster/.config /home/tobster/.wallpapers"
    )


def setup_system_basics():
    try:
        execute_command("sed -i '/\\[multilib\\]/,+1 s/^#//' /etc/pacman.conf")
        execute_command("pacman -Syy")
        execute_command("pacman -S --needed --noconfirm flatpak")
        execute_command(
            "flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo"
        )
        print("-> Multilib + Flathub enabled.")
    except subprocess.CalledProcessError:
        print("Failed to enable multilib/flatpak.")

    try:
        execute_command("useradd -m -G wheel -s /bin/zsh tobster")
        execute_command("echo 'tobster:password' | chpasswd")
        execute_command(
            "sed -i 's/# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers"
        )
        print("-> User 'tobster' created and NOPASSWD set.")
    except subprocess.CalledProcessError:
        print("-> User 'tobster' may already exist. Ensuring NOPASSWD is set...")
        execute_command(
            "sed -i 's/# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers"
        )
        execute_command(
            "sed -i 's/%wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers"
        )

    try:
        execute_command("systemctl enable NetworkManager")
        print("-> NetworkManager enabled.")
    except subprocess.CalledProcessError:
        print("Failed to enable NetworkManager.")

    setup_locale()


def setup_locale():
    print("\nSetting system locale to English...")
    try:
        execute_command(
            "sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen"
        )
        execute_command(
            "sed -i 's/#de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen"
        )
        execute_command("locale-gen")

        with open("/etc/locale.conf", "w") as f:
            f.write("LANG=en_US.UTF-8\n")
            f.write("LC_TIME=en_US.UTF-8\n")
            f.write("LC_MESSAGES=en_US.UTF-8\n")

        execute_command("mkdir -p /home/tobster/.config/locale")
        with open("/home/tobster/.config/locale.conf", "w") as f:
            f.write("LANG=en_US.UTF-8\n")
        execute_command("chown tobster:tobster /home/tobster/.config/locale.conf")

        if not os.path.exists("/etc/vconsole.conf"):
            with open("/etc/vconsole.conf", "w") as f:
                f.write("KEYMAP=de\n")
        else:
            execute_command(
                "grep -q 'KEYMAP' /etc/vconsole.conf || echo 'KEYMAP=de' >> /etc/vconsole.conf"
            )

        print("-> System locale set to en_US.UTF-8 (keyboard layout stays German).")
    except Exception as e:
        print(f"Failed to set locale: {e}")


def setup_firewall():
    print("\nConfiguring UFW Firewall...")
    try:
        pacman_install("ufw")
        execute_command("ufw default deny incoming")
        execute_command("ufw default allow outgoing")
        execute_command("ufw allow 53317/tcp")
        execute_command("ufw allow 53317/udp")
        execute_command("ufw logging on")
        execute_command("ufw --force enable")
        execute_command("systemctl enable ufw.service")
        print("-> Firewall activated and configured.")
    except Exception as e:
        print(f"Failed to setup firewall: {e}")


def setup_opsec():
    print("\nApplying Security Hardening (OpSec)...")
    sysctl_conf = """# Restrict dmesg access to root
kernel.dmesg_restrict = 1

# Enable TCP syncookies (prevents SYN flood attacks)
net.ipv4.tcp_syncookies = 1

# Ignore ICMP echo requests (Ping)
net.ipv4.icmp_echo_ignore_all = 1
"""
    try:
        with open("/etc/sysctl.d/99-opsec.conf", "w") as f:
            f.write(sysctl_conf)
        execute_command("sysctl --system")

        with open("/etc/profile.d/99-umask.sh", "w") as f:
            f.write("umask 027\n")
        execute_command("chmod +x /etc/profile.d/99-umask.sh")
        print("-> Sysctl network limits and Umask 027 applied.")
    except Exception as e:
        print(f"Failed to apply OpSec: {e}")


def picom_config():
    config_dir = "/home/tobster/.config/picom"
    execute_command(f"mkdir -p {config_dir}")
    with open(f"{config_dir}/picom.conf", "w") as f:
        f.write(picom_content)
    execute_command("chown -R tobster:tobster /home/tobster/.config/picom")
    print("-> Picom config installed.")


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
            execute_command(
                f'sed -i \'s/interface="wlan0"/interface="{interface}"/\' {config_path}'
            )
            print(f"-> WiFi interface '{interface}' patched into qtile config.")
        else:
            print("-> No WiFi interface found, leaving 'wlan0' as default.")
    except subprocess.CalledProcessError:
        print("-> Could not detect WiFi interface.")


def setup_cursor():
    print("\nSetting up cursor theme...")
    gtk_dir = "/home/tobster/.config/gtk-3.0"
    execute_command(f"mkdir -p {gtk_dir}")
    with open(f"{gtk_dir}/settings.ini", "w") as f:
        f.write(gtk_settings_content)

    with open("/home/tobster/.gtkrc-2.0", "w") as f:
        f.write('gtk-cursor-theme-name="Bibata-Modern-Classic"\n')
        f.write("gtk-cursor-theme-size=24\n")

    with open("/home/tobster/.Xresources", "w") as f:
        f.write(xresources_content)

    execute_command("mkdir -p /usr/share/icons/default")
    with open("/usr/share/icons/default/index.theme", "w") as f:
        f.write("[Icon Theme]\nInherits=Bibata-Modern-Classic\n")

    execute_command("chown -R tobster:tobster /home/tobster/.config/gtk-3.0")
    execute_command("chown tobster:tobster /home/tobster/.Xresources")
    execute_command("chown tobster:tobster /home/tobster/.gtkrc-2.0")
    print("-> Cursor theme configured (Bibata-Modern-Classic).")


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

    scripts = {
        "qtile_reload.sh": wal_postscript_content,
        "starship_reload.sh": starship_wal_postscript_content,
        "cursor_reload.sh": cursor_wal_postscript_content,
        "rofi_reload.sh": rofi_wal_postscript_content,
        "ly_reload.sh": ly_wal_postscript_content,
        "gtk_wal_reload.sh": gtk_wal_postscript_content,
        "alacritty_reload.sh": alacritty_wal_postscript_content,
    }
    for filename, content in scripts.items():
        with open(f"{postscript_dir}/{filename}", "w") as f:
            f.write(content)
        execute_command(f"chmod +x {postscript_dir}/{filename}")
        print(f"-> pywal postscript '{filename}' installed.")

    execute_command("chown -R tobster:tobster /home/tobster")


def setup_alacritty():
    config_dir = "/home/tobster/.config/alacritty"
    execute_command(f"mkdir -p {config_dir}")

    with open(f"{config_dir}/alacritty.toml", "w") as f:
        f.write(alacritty_content)

    with open(f"{config_dir}/colors-live.toml", "w") as f:
        f.write("# Fallback empty config until pywal runs\n")

    template_dir = "/home/tobster/.config/wal/templates"
    execute_command(f"mkdir -p {template_dir}")
    with open(f"{template_dir}/colors-alacritty.toml", "w") as f:
        f.write(alacritty_wal_template)

    execute_command("chown -R tobster:tobster /home/tobster/.config/alacritty")
    execute_command("chown -R tobster:tobster /home/tobster/.config/wal")
    print("-> Alacritty configured with pywal integration.")


def setup_rofi():
    config_dir = "/home/tobster/.config/rofi"
    execute_command(f"mkdir -p {config_dir}")
    with open(f"{config_dir}/config.rasi", "w") as f:
        f.write(rofi_content)
    execute_command(f"chown -R tobster:tobster {config_dir}")
    print("-> Rofi configured with pywal color integration.")


def setup_ly():
    print("\nSetting up Ly display manager...")
    try:
        ly_config_dir = "/etc/ly"
        execute_command(f"mkdir -p {ly_config_dir}")
        with open(f"{ly_config_dir}/config.ini", "w") as f:
            f.write(ly_config_content)
        execute_command("systemctl disable getty@tty2.service 2>/dev/null || true")
        execute_command("systemctl enable ly@tty2.service")
        print("-> Ly enabled on TTY2.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to setup Ly: {e}")


def setup_pipewire():
    service_dir = "/home/tobster/.config/systemd/user"
    wants_dir = f"{service_dir}/default.target.wants"
    execute_command(f"mkdir -p {wants_dir}")

    for service in [
        "pipewire.service",
        "pipewire-pulse.service",
        "wireplumber.service",
    ]:
        execute_command(f"ln -sf /usr/lib/systemd/user/{service} {wants_dir}/{service}")
    execute_command("chown -R tobster:tobster /home/tobster/.config/systemd")
    print("-> Pipewire enabled via symlinks.")


def setup_zsh():
    zshrc_src = "/tmp/OS_config/zsh/zsh.zshrc"
    zshrc_dst = "/home/tobster/.zshrc"
    try:
        execute_command(
            "grep -qxF '/bin/zsh' /etc/shells || echo '/bin/zsh' >> /etc/shells"
        )
        execute_command(f"cp {zshrc_src} {zshrc_dst}")
        execute_command(f"chown tobster:tobster {zshrc_dst}")
        execute_command("usermod -s /bin/zsh tobster")
        execute_command(
            "sed -i 's|\\(tobster:x:[^:]*:[^:]*:[^:]*:[^:]*:\\)/bin/bash|\\1/bin/zsh|' /etc/passwd"
        )
        print("-> Zsh configured and set as default shell.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not setup Zsh properly. Error: {e}")


def setup_starship():
    config_dir = "/home/tobster/.config"
    execute_command(f"mkdir -p {config_dir}")
    with open(f"{config_dir}/starship.toml", "w") as f:
        f.write(starship_content)
    execute_command(f"chown tobster:tobster {config_dir}/starship.toml")
    print("-> Starship configured.")


def load_wallpapers_to_folders():
    execute_command("mkdir -p /home/tobster/.wallpapers")
    execute_command(
        "git clone https://github.com/phenax/wallpapers.git /home/tobster/.wallpapers"
    )
    execute_command("chown -R tobster:tobster /home/tobster/.wallpapers")
    print("-> Wallpapers loaded.")


def setup_bluetooth():
    execute_command("systemctl enable bluetooth.service")
    print("-> Bluetooth enabled.")


def setup_networkmanager():
    execute_command("systemctl enable NetworkManager.service")
    print("-> NetworkManager enabled.")


# <<<-----------------------------------------------------------MAIN---------------------------------------------------------->>>


def main():
    try:
        setup_system_basics()
        setup_opsec()
        setup_firewall()
        install_before_packages()
        install_yay()
        install_packages()
        install_aur_packages()
        install_eww()
        install_oh_my_zsh()
        qtile_config()
        detect_wifi_interface()
        picom_config()
        load_wallpapers_to_folders()
        setup_pipewire()
        setup_bluetooth()
        setup_networkmanager()
        setup_cursor()
        setup_alacritty()
        setup_rofi()
        setup_ly()
        setup_zsh()
        setup_starship()
        autostart()
        execute_command(
            "pacman -S --needed --noconfirm python-psutil python-iwlib alsa-utils"
        )

    finally:
        print("\nRestoring sudo security settings...")
        execute_command(
            "sed -i 's/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers"
        )
        print("-> Sudo password requirement for 'tobster' re-enabled.")

    print("\n--- Process Finished ---")
    if failed_packages:
        print(f"Failed to install: {', '.join(failed_packages)}")
    else:
        print("Everything installed! Reboot — Ly will greet you.")


if __name__ == "__main__":
    main()
