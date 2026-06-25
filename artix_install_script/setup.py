import subprocess
import os

# <<<-----------------------------------------------------------HYPERPARAMETERS---------------------------------------------------------->>>
TIMEOUT = 10000
USER = "tobster"
HOME = f"/home/{USER}"
REPO_URL = "https://github.com/tobiastettenborn193-prog/OS.git"
REPO_DIR = "/tmp/OS_config"
failed_packages = []

# <<<-----------------------------------------------------------PACKAGE LISTS---------------------------------------------------------->>>
before_packages = [
    "git",
    "base-devel",
    "reflector",
    "artix-archlinux-support",
]

wayland_packages = [
    "niri",
    "xwayland-satellite",
    "waybar",
    "fuzzel",
    "mako",
    "swaybg",
    "swaylock",
    "xdg-desktop-portal-gtk",
    "xdg-desktop-portal-gnome",
    "qt5-wayland",
    "qt6-wayland",
    "polkit",
    "polkit-gnome",
    "gnome-keyring",
    # elogind + elogind-runit schon vom install.py dabei
]

# greetd-tuigreet ist AUR -> kommt in aur_packages
dm_packages = [
    "greetd",
]

audio_packages = [
    "pipewire",
    "pipewire-pulse",
    "pipewire-alsa",
    "pipewire-jack",
    "wireplumber",
    "pavucontrol",
    "playerctl",
    "alsa-utils",
]

shell_packages = [
    "alacritty",
    "zsh",
    "starship",
    "fzf",
    "yazi",
    "btop",
    "fastfetch",
]

font_packages = [
    "ttf-jetbrains-mono-nerd",
]

gtk_packages = [
    "papirus-icon-theme",
    "brightnessctl",
]

dev_packages = [
    "python",
    "python-pip",
    "python-psutil",
    "rust",
    "go",
    "nano",
    "unzip",
    "jdk17-openjdk",
    "esptool",
    # code (VSCode) und uv sind AUR auf Artix -> aur_packages
]

gaming_packages = [
    "steam",
    "lib32-vulkan-nouveau",
    "vulkan-nouveau",
    "lib32-libva-mesa-driver",
    "libva-mesa-driver",
    "prismlauncher",
]

security_packages = [
    "ufw",
    "wireshark-qt",
]

misc_packages = [
    "flatpak",
    "wl-clipboard",
    "grim",
    "slurp",
    "libnotify",
    "obsidian",
    "bluez",
    "bluez-utils",
    "bluez-runit",
    "networkmanager-runit",
    "tailscale",
    "tailscale-runit",
    "nemo",
    "nemo-fileroller",
]

# Alles AUR
aur_packages = [
    "greetd-tuigreet",
    "code",
    "uv",
    "zen-browser-bin",
    "librewolf-bin",
    "vesktop-bin",
    "ollama-bin",
    "bibata-cursor-theme-bin",
    "localsend-bin",
    "mullvad-vpn-bin",
    "zellij",
    "python-pywal",
    # oh-my-zsh via curl in setup_zsh()
]

# <<<-----------------------------------------------------------ENV---------------------------------------------------------->>>
TOBSTER_ENV = {
    "HOME": HOME,
    "USER": USER,
    "LOGNAME": USER,
    "PATH": f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{HOME}/.local/bin:{HOME}/go/bin:{HOME}/.cargo/bin",
    "TERM": "xterm",
    "GOPATH": f"{HOME}/go",
    "GOCACHE": f"{HOME}/.cache/go",
    "GOPROXY": "https://proxy.golang.org,direct",
    "XDG_CACHE_HOME": f"{HOME}/.cache",
    "XDG_RUNTIME_DIR": "/run/user/1000",
}

# <<<-----------------------------------------------------------HELPERS---------------------------------------------------------->>>
def run(cmd: str, check: bool = True) -> str:
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=TIMEOUT
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.stdout

def run_as_user(cmd: str) -> str:
    result = subprocess.run(
        ["sudo", "-u", USER, "bash", "-c", f"HOME={HOME} {cmd}"],
        capture_output=True, text=True, timeout=TIMEOUT, env=TOBSTER_ENV,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.stdout

def pacman(package: str):
    print(f"[pacman] {package}")
    try:
        run(f"pacman -S --needed --noconfirm {package}")
    except Exception as e:
        print(f"  -> FEHLER: {e}")
        failed_packages.append(package)

def paru(package: str):
    print(f"[paru] {package}")
    try:
        result = subprocess.run(
            ["sudo", "-u", USER, "paru", "-S", "--needed", "--noconfirm",
             "--answerclean", "None", "--answerdiff", "None", package],
            capture_output=True, text=True, timeout=TIMEOUT, env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            print(f"  -> FEHLER (paru): {result.stderr[-500:]}")
            failed_packages.append(package)
    except Exception as e:
        print(f"  -> FEHLER: {e}")
        failed_packages.append(package)

def smart_install(package: str):
    try:
        run(f"pacman -S --needed --noconfirm {package}")
        print(f"[pacman] {package} ok")
    except Exception:
        paru(package)

def write_file(path: str, content: str, owner: str = None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write(content)
    if owner:
        run(f"chown {owner}:{owner} {path}")

# <<<-----------------------------------------------------------SETUP FUNCTIONS---------------------------------------------------------->>>
def set_temporary_sudo():
    print("\n=== Temporaere Sudo-Rechte setzen ===")
    run("mkdir -p /etc/sudoers.d")
    write_file("/etc/sudoers.d/99-installer-nopasswd", "%wheel ALL=(ALL:ALL) NOPASSWD: ALL\n")
    run("chmod 0440 /etc/sudoers.d/99-installer-nopasswd")

def update_mirrors():
    print("\n=== Mirrors aktualisieren ===")
    try:
        run("reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist")
        run("pacman -Syy")
    except Exception as e:
        print(f"-> Warnung: {e}")

def install_base_packages():
    print("\n=== Basis-Pakete ===")
    for pkg in before_packages:
        pacman(pkg)

def enable_arch_repos():
    print("\n=== Arch-Repos aktivieren ===")
    try:
        with open("/etc/pacman.conf", "r") as f:
            content = f.read()
        if "[extra]" not in content:
            with open("/etc/pacman.conf", "a") as f:
                f.write("\n[extra]\nInclude = /etc/pacman.d/mirrorlist-arch\n")
                f.write("\n[multilib]\nInclude = /etc/pacman.d/mirrorlist-arch\n")
            run("pacman-key --populate archlinux")
            run("pacman -Syy")
            print("-> Arch-Repos aktiviert.")
        else:
            print("-> Arch-Repos schon aktiv.")
    except Exception as e:
        print(f"-> Warnung: {e}")

def install_paru():
    print("\n=== paru installieren ===")
    build_dir = f"{HOME}/.cache/paru-build"
    try:
        run(f"rm -rf {build_dir}")
        run(f"mkdir -p {build_dir}")
        run(f"chown -R {USER}:{USER} {build_dir}")
        result = subprocess.run(
            ["sudo", "-u", USER, "bash", "-c",
             f"cd {build_dir} && git clone https://aur.archlinux.org/paru-bin.git . && makepkg -si --noconfirm"],
            capture_output=True, text=True, timeout=TIMEOUT, env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            print(f"  -> FEHLER: {result.stderr}")
            failed_packages.append("paru")
        else:
            print("-> paru ok.")
    except Exception as e:
        print(f"-> FEHLER: {e}")
        failed_packages.append("paru")

def install_package_groups():
    print("\n=== Pakete installieren ===")
    all_pacman = (
        wayland_packages + dm_packages + audio_packages +
        shell_packages + font_packages + gtk_packages +
        dev_packages + gaming_packages + security_packages + misc_packages
    )
    for pkg in all_pacman:
        smart_install(pkg)
    print("\n=== AUR-Pakete ===")
    for pkg in aur_packages:
        paru(pkg)

def setup_system():
    print("\n=== System-Einstellungen ===")
    try:
        run("sed -i '/\\[multilib\\]/,+1 s/^#//' /etc/pacman.conf")
        run("pacman -Syy")
    except Exception:
        pass
    try:
        run("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo")
    except Exception:
        pass
    try:
        run(f"useradd -m -G wheel,video,audio,input,uucp -s /bin/zsh {USER}")
    except Exception:
        run(f"usermod -aG wheel,video,audio,input,uucp {USER}")
    try:
        run("grep -q '^dialout:' /etc/group || groupadd dialout")
        run(f"usermod -aG dialout {USER}")
    except Exception:
        pass
    run("sed -i 's/#de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen")
    run("sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen")
    run("locale-gen")
    write_file("/etc/locale.conf", "LANG=de_DE.UTF-8\n")
    run("localectl set-keymap de")
    for svc in ["NetworkManager", "bluetoothd", "tailscaled", "elogind"]:
        try:
            run(f"ln -sf /etc/runit/sv/{svc} /etc/runit/runsvdir/default/{svc}")
        except Exception:
            print(f"Warnung: Service {svc} nicht verlinkt.")

def setup_pipewire():
    print("\n=== Pipewire User-Services ===")
    sv_base = f"{HOME}/.runit/sv"
    run_base = f"{HOME}/.runit/runsvdir"
    for svc in ["pipewire", "pipewire-pulse", "wireplumber"]:
        sv_dir = f"{sv_base}/{svc}"
        os.makedirs(sv_dir, exist_ok=True)
        write_file(f"{sv_dir}/run", f"#!/bin/sh\nexec {svc}\n")
        run(f"chmod +x {sv_dir}/run")
        run(f"mkdir -p {run_base}")
        run(f"ln -sf {sv_base}/{svc} {run_base}/{svc}")
    run(f"chown -R {USER}:{USER} {HOME}/.runit")
    zprofile = f"{HOME}/.zprofile"
    with open(zprofile, "a") as f:
        f.write("\n# Runit User Services\nexport SVDIR=~/.runit/runsvdir\nrunsvdir -P ~/.runit/runsvdir &\n")
    run(f"chown {USER}:{USER} {zprofile}")

def setup_greetd():
    print("\n=== greetd ===")
    try:
        run("useradd -M -G video -s /bin/sh greeter")
    except Exception:
        pass
    run("mkdir -p /etc/greetd")
    write_file("/etc/greetd/config.toml",
        "[terminal]\nvt = 1\n\n[default_session]\n"
        'command = "tuigreet --time --remember --sessions /usr/share/wayland-sessions --asterisks"\n'
        'user = "greeter"\n'
    )
    # Artix-Paket legt /etc/runit/sv/greetd schon an -> nur symlinken
    try:
        run("ln -sf /etc/runit/sv/greetd /etc/runit/runsvdir/default/greetd")
    except Exception:
        pass
    run("rm -f /etc/runit/runsvdir/default/agetty-tty1")

def setup_firewall():
    print("\n=== UFW ===")
    try:
        run("ufw default deny incoming")
        run("ufw default allow outgoing")
        run("ufw allow 53317/tcp")
        run("ufw allow 53317/udp")
        run("ufw logging on")
        run("ufw --force enable")
        run("ln -sf /etc/runit/sv/ufw /etc/runit/runsvdir/default/ufw")
    except Exception as e:
        print(f"-> Warnung: {e}")

def setup_opsec():
    print("\n=== Security Hardening ===")
    try:
        write_file("/etc/sysctl.d/99-opsec.conf",
            "kernel.dmesg_restrict = 1\nnet.ipv4.tcp_syncookies = 1\nnet.ipv4.icmp_echo_ignore_all = 1\n")
        run("sysctl --system")
        write_file("/etc/profile.d/99-umask.sh", "umask 027\n")
        run("chmod +x /etc/profile.d/99-umask.sh")
    except Exception as e:
        print(f"-> Warnung: {e}")

def clone_dotfiles():
    print("\n=== Dotfiles clonen ===")
    run(f"rm -rf {REPO_DIR}")
    run(f"git clone {REPO_URL} {REPO_DIR}")

def symlink_configs():
    print("\n=== Configs symlinken ===")
    config_dir = f"{HOME}/.config"
    run(f"mkdir -p {config_dir}")
    links = {
        f"{REPO_DIR}/niri":           f"{config_dir}/niri",
        f"{REPO_DIR}/waybar":         f"{config_dir}/waybar",
        f"{REPO_DIR}/fuzzel":         f"{config_dir}/fuzzel",
        f"{REPO_DIR}/zsh/zsh.zshrc": f"{HOME}/.zshrc",
    }
    for src, dst in links.items():
        if os.path.exists(src):
            run(f"rm -rf {dst}")
            run(f"ln -sf {src} {dst}")
        else:
            print(f"  Warnung: {src} nicht gefunden.")
    run(f"chown -R {USER}:{USER} {config_dir}")

def setup_alacritty():
    print("\n=== Alacritty ===")
    config_dir = f"{HOME}/.config/alacritty"
    run(f"mkdir -p {config_dir}")
    write_file(f"{config_dir}/alacritty.toml", """[general]
import = ["~/.cache/wal/colors-alacritty.toml"]

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
""", USER)
    run(f"chown -R {USER}:{USER} {config_dir}")

def setup_gtk():
    print("\n=== GTK Settings ===")
    gtk_dir = f"{HOME}/.config/gtk-3.0"
    run(f"mkdir -p {gtk_dir}")
    write_file(f"{gtk_dir}/settings.ini", """[Settings]
gtk-theme-name=Adwaita-dark
gtk-icon-theme-name=Papirus-Dark
gtk-font-name=JetBrainsMono Nerd Font 10
gtk-cursor-theme-name=Bibata-Modern-Classic
gtk-cursor-theme-size=24
gtk-xft-antialias=1
gtk-xft-hinting=1
gtk-xft-hintstyle=hintslight
gtk-xft-rgba=rgb
""", USER)
    write_file(f"{HOME}/.Xresources", "Xcursor.theme: Bibata-Modern-Classic\nXcursor.size: 24\n", USER)
    run("mkdir -p /usr/share/icons/default")
    write_file("/usr/share/icons/default/index.theme", "[Icon Theme]\nInherits=Bibata-Modern-Classic\n")
    run(f"chown -R {USER}:{USER} {gtk_dir}")

def setup_starship():
    print("\n=== Starship ===")
    # raw string damit {} nicht als f-string interpoliert werden
    content = r""""$schema" = 'https://starship.rs/config-schema.json'
format = """
[┌─](bold)$directory$git_branch$git_status$git_metrics
[└─](bold)$python$rust$nodejs$cmd_duration$character"""

[directory]
style = "bold blue"
truncation_length = 3
truncate_to_repo = true
format = "[ $path ]($style)[$read_only]($read_only_style) "

[git_branch]
symbol = " "
format = "[on](#) [$symbol$branch]($style) "

[git_status]
format = '([$all_status$ahead_behind]($style) )'
conflicted = "⚡"
ahead = "⇡${count}"
behind = "⇣${count}"
modified = "✎${count}"
untracked = "?${count}"
staged = "+${count}"
deleted = "✘${count}"

[git_metrics]
disabled = false

[python]
symbol = " "
format = '[${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'

[rust]
symbol = " "

[nodejs]
symbol = " "

[cmd_duration]
min_time = 2_000
format = "[⏱ $duration]($style) "

[character]
success_symbol = "[❯](green)"
error_symbol = "[❯](red)"
"""
    write_file(f"{HOME}/.config/starship.toml", content, USER)

def setup_zsh():
    print("\n=== ZSH ===")
    try:
        run("grep -qxF '/bin/zsh' /etc/shells || echo '/bin/zsh' >> /etc/shells")
        run(f"usermod -s /bin/zsh {USER}")
    except Exception as e:
        print(f"-> Warnung: {e}")
    try:
        result = subprocess.run(
            ["sudo", "-u", USER, "bash", "-c",
             f'HOME={HOME} RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'],
            capture_output=True, text=True, timeout=TIMEOUT, env=TOBSTER_ENV,
        )
        if result.returncode != 0:
            print(f"-> oh-my-zsh FEHLER: {result.stderr[-300:]}")
            failed_packages.append("oh-my-zsh")
        else:
            for url, name in [
                ("https://github.com/zsh-users/zsh-autosuggestions", "zsh-autosuggestions"),
                ("https://github.com/zsh-users/zsh-syntax-highlighting.git", "zsh-syntax-highlighting"),
            ]:
                run_as_user(f"git clone {url} {HOME}/.oh-my-zsh/custom/plugins/{name}")
    except Exception as e:
        print(f"-> Warnung oh-my-zsh: {e}")

def setup_wallpapers():
    print("\n=== Wallpapers ===")
    src = f"{REPO_DIR}/wallpapers"
    dst = f"{HOME}/.wallpapers"
    if os.path.exists(src):
        run(f"mkdir -p {dst}")
        run(f"cp -r {src}/. {dst}/")
        run(f"chown -R {USER}:{USER} {dst}")
    else:
        print("-> wallpapers/ nicht im Repo.")

def setup_mullvad():
    print("\n=== Mullvad VPN ===")
    try:
        run("ln -sf /etc/runit/sv/mullvad-daemon /etc/runit/runsvdir/default/mullvad-daemon")
    except Exception as e:
        print(f"-> Warnung: {e}")

def create_helper_scripts():
    print("\n=== Helper Scripts ===")
    bin_dir = f"{HOME}/.local/bin"
    run(f"mkdir -p {bin_dir}")
    # raw strings damit Shell-Variablen nicht interpoliert werden
    write_file(f"{bin_dir}/volume.sh", r"""#!/bin/bash
case "$1" in
    up)   pactl set-sink-volume @DEFAULT_SINK@ +5% ;;
    down) pactl set-sink-volume @DEFAULT_SINK@ -5% ;;
    mute) pactl set-sink-mute @DEFAULT_SINK@ toggle ;;
esac
VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -n1)
MUTE=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -i yes)
if [ -n "$MUTE" ]; then
    notify-send -h string:x-mako-tag:volume -a "Volume" "Muted" -i audio-volume-muted
else
    notify-send -h string:x-mako-tag:volume -h int:value:"$VOL" -a "Volume" "Volume: ${VOL}%" -i audio-volume-high
fi
""")
    write_file(f"{bin_dir}/powermenu.sh", r"""#!/bin/bash
chosen=$(printf "Shutdown\nReboot\nSuspend\nLock\nLogout" | fuzzel --dmenu --prompt "Power  ")
case "$chosen" in
    Shutdown) loginctl poweroff ;;
    Reboot)   loginctl reboot ;;
    Suspend)  loginctl suspend ;;
    Lock)     swaylock ;;
    Logout)   niri msg action quit ;;
esac
""")
    run(f"chmod +x {bin_dir}/volume.sh {bin_dir}/powermenu.sh")
    run(f"chown -R {USER}:{USER} {HOME}/.local")

def setup_fuzzel_template():
    print("\n=== Fuzzel Pywal Template ===")
    template_dir = f"{HOME}/.config/wal/templates"
    run(f"mkdir -p {template_dir}")
    # Kein f-String - Pywal verarbeitet {} selbst
    write_file(f"{template_dir}/colors-fuzzel.ini",
        "[colors]\n"
        "background={background.strip}e6\n"
        "text={foreground.strip}ff\n"
        "match={color4.strip}ff\n"
        "selection={color4.strip}e6\n"
        "selection-text={background.strip}ff\n"
        "selection-match={color1.strip}ff\n"
        "border={color4.strip}ff\n",
        USER
    )

# <<<-----------------------------------------------------------MAIN---------------------------------------------------------->>>
def main():
    try:
        set_temporary_sudo()
        update_mirrors()
        install_base_packages()
        enable_arch_repos()
        install_paru()
        install_package_groups()
        setup_system()
        setup_pipewire()
        setup_greetd()
        setup_firewall()
        setup_opsec()
        clone_dotfiles()
        symlink_configs()
        setup_alacritty()
        setup_gtk()
        setup_starship()
        setup_zsh()
        setup_wallpapers()
        setup_mullvad()
        setup_fuzzel_template()
        create_helper_scripts()
    finally:
        print("\n=== Sudo-Sicherheit wiederherstellen ===")
        run("rm -f /etc/sudoers.d/99-installer-nopasswd")

    print("\n" + "=" * 50)
    if failed_packages:
        print(f"Fehlgeschlagen: {', '.join(failed_packages)}")
    else:
        print("Alles erfolgreich! Reboot -> greetd begruesst dich.")
    print("=" * 50)

if __name__ == "__main__":
    main()
