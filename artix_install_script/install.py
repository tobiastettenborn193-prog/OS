import os
import subprocess
import sys
import getpass  # Für die sichere, unsichtbare Passworteingabe

# <<<--------------------------------------------------------------HYPERPARAMETERS------------------------------------------------------------>>>>

Timeout = 300
system_name = "Artix"
profile_name = "tobster"

# HINWEIS: Passwörter werden jetzt beim Start sicher abgefragt!
profile_password = ""
root_password = ""

keyboard_layout = "de-latin1"
timezone = "Europe/Berlin"

# Der RAW-Link zu deinem Stufe-2-Skript auf GitHub
SETUP_SCRIPT_URL = "https://raw.githubusercontent.com/tobiastettenborn193-prog/OS/main/artix_install_script/setup.py"

# <<<--------------------------------------------------------------DISK SELECTION------------------------------------------------------------>>>>

print("---------------Scanning available disks---------------------")
result = subprocess.run(
    "lsblk -d -n -o NAME,SIZE,MODEL", shell=True, capture_output=True, text=True
)
print(result.stdout)

Drive = input("Welches Laufwerk soll verwendet werden? (z.B. /dev/nvme0n1 oder /dev/sda): ").strip()

if not Drive.startswith("/dev/"):
    Drive = f"/dev/{Drive}"

print(f"Selected drive: {Drive}")
print("---------------Disk selected---------------------")
print("\n" * 2)

if "nvme" in Drive:
    boot_part = f"{Drive}p1"
    root_part = f"{Drive}p2"
else:
    boot_part = f"{Drive}1"
    root_part = f"{Drive}2"

# <<<--------------------------------------------------------------FUNCTIONS------------------------------------------------------------>>>>

def execute_command(command: str):
    subprocess.run(command, shell=True, timeout=Timeout, check=True)

def setup_base_system():
    print("---------------Configuring keyboard layout and timezone---------------------")
    execute_command(f"loadkeys {keyboard_layout}")
    execute_command(f"timedatectl set-timezone {timezone}")
    print("Keyboard layout: " + keyboard_layout)
    print("Timezone: " + timezone)
    print("---------------Keyboard layout and timezone configured---------------------")
    
    print("\n---------------Harddrive partitions---------------------")
    execute_command(
        f'sgdisk --clear --new=1:0:+1G --typecode=1:ef00 --change-name=1:"EFI" --new=2:0:0 --typecode=2:8300 --change-name=2:"ROOT" {Drive}'
    )
    
    print("\n---------------Formatting partitions---------------------")
    execute_command(f"mkfs.vfat -F 32 {boot_part}")
    execute_command(f"mkfs.ext4 {root_part}")
    
    print("\n---------------Mounting partitions---------------------")
    execute_command(f"mount {root_part} /mnt")
    execute_command(f"mkdir -p /mnt/boot")
    execute_command(f"mount {boot_part} /mnt/boot")
    
    print("\n---------------Installing base system---------------------")
    execute_command(
        "basestrap /mnt base base-devel runit elogind-runit linux linux-firmware "
        "networkmanager networkmanager-runit nano sudo python git curl"
    )
    
    print("\n---------------Generating fstab---------------------")
    execute_command("fstabgen -U /mnt >> /mnt/etc/fstab")
    print("DONE WITH THE BASE SYSTEM SETUP\n")


def copy_setup_script():
    """Lädt setup.py direkt von GitHub in das neue System herunter"""
    print("\n---------------Downloading setup.py from GitHub---------------------")
    
    dest_dir = f"/mnt/home/{profile_name}"
    dest_file = f"{dest_dir}/setup.py"

    execute_command(f"mkdir -p {dest_dir}")
    execute_command(f"curl -sL {SETUP_SCRIPT_URL} -o {dest_file}")
    
    print(f"-> setup.py erfolgreich heruntergeladen nach {dest_file}")


def install_autostart_service():
    """Legt den temporären runit-Oneshot-Service für den ersten Boot an."""
    print("\n---------------Installing first-boot runit service---------------------")

    service_dir = "/mnt/etc/runit/sv/first-boot-setup"
    os.makedirs(service_dir, exist_ok=True)

    run_script = f"""#!/bin/sh
if [ -f /home/{profile_name}/setup.py ]; then
    /usr/bin/python3 /home/{profile_name}/setup.py
    # Service nach erfolgreichem Run selbst entfernen
    rm -f /home/{profile_name}/setup.py
    rm -rf /etc/runit/runsvdir/default/first-boot-setup
fi
sv down first-boot-setup
"""
    run_path = f"{service_dir}/run"
    with open(run_path, "w", newline="\n") as f:
        f.write(run_script)
    execute_command(f"chmod +x {run_path}")

    wants_dir = "/mnt/etc/runit/runsvdir/default"
    execute_command(f"mkdir -p {wants_dir}")
    execute_command(f"ln -sf /etc/runit/sv/first-boot-setup {wants_dir}/first-boot-setup")
    print("-> first-boot-setup runit service installiert.")


def configure_chroot():
    print("\n---------------Configuring chroot---------------------")
    chroot_script = f"""#!/bin/bash
set -ex

# Zeitzone und Locales
ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime
hwclock --systohc
echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=de_DE.UTF-8" > /etc/locale.conf
echo "KEYMAP={keyboard_layout}" > /etc/vconsole.conf

# Hostname
echo "{system_name}" > /etc/hostname

# Root Passwort setzen
echo "root:{root_password}" | chpasswd

# User erstellen
if ! id "{profile_name}" &>/dev/null; then
    useradd -m -G wheel -s /bin/bash {profile_name}
fi
echo "{profile_name}:{profile_password}" | chpasswd

# Ownership von setup.py setzen
chown {profile_name}:{profile_name} /home/{profile_name}/setup.py 2>/dev/null || true

# Sudo aktivieren
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers

# Netzwerk für Stufe 2 aktivieren
ln -sf /etc/runit/sv/NetworkManager /etc/runit/runsvdir/default/NetworkManager

# Keyrings initialisieren
pacman-key --init
pacman-key --populate artix

# Bootloader (GRUB) installieren
pacman -S --noconfirm grub efibootmgr
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
"""
    execute_command("mkdir -p /mnt/root")
    chroot_script_path = "/mnt/root/chroot_setup.sh"
    with open(chroot_script_path, "w", newline="\n") as f:
        f.write(chroot_script)

    execute_command(f"chmod +x {chroot_script_path}")
    execute_command(f"artix-chroot /mnt /root/chroot_setup.sh")
    execute_command("rm /mnt/root/chroot_setup.sh")
    print("DONE WITH THE CHROOT CONFIGURATION\n")


def finalize_installation():
    print("\n---------------Cleaning up and unmounting partitions---------------------")
    execute_command("umount -R /mnt")
    print("=" * 50)
    print("INSTALLATION ENTIRELY COMPLETE!")
    print("You can now safely type 'reboot' to restart your PC.")
    print("=" * 50)

# <<<--------------------------------------------------------------MAIN------------------------------------------------------------>>>>

if __name__ == "__main__":
    print("\n=== Sicherheitsabfrage: Passwörter festlegen ===")
    print("Hinweis: Aus Sicherheitsgründen werden die Zeichen beim Tippen NICHT angezeigt.\n")
    
    # Sichere Abfrage der Passwörter zur Laufzeit
    profile_password = getpass.getpass(f"Bitte Passwort für den neuen User '{profile_name}' eingeben: ")
    root_password = getpass.getpass("Bitte Passwort für den System-Administrator 'root' eingeben: ")

    # Kurzer Check, damit man nicht aus Versehen Enter drückt und ein leeres Passwort setzt
    if not profile_password or not root_password:
        print("\n[!] FEHLER: Die Passwörter dürfen nicht leer sein. Installation abgebrochen.")
        sys.exit(1)
        
    print("\nPasswörter temporär im RAM gespeichert. Starte Installation...\n")

    # Der restliche Ablauf bleibt exakt gleich
    setup_base_system()
    copy_setup_script()
    install_autostart_service()
    configure_chroot()
    finalize_installation()