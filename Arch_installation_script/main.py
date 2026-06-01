#<<<--------------------------------------------------------------IMPORTS------------------------------------------------------------>>>>
import subprocess
import sys
import os

#<<<--------------------------------------------------------------HYPERPARAMETERS------------------------------------------------------------>>>>

Timeout = 300
system_name = "Arch"
profile_name = "username"
profile_password = "YourPassword123!"
root_password = "YourRootPassword123!"
keyboard_layout = "de-latin1"
timezone = "Europe/Berlin"

# Pfad zu setup.py auf dem ISO (airootfs/root/ wird nach /root/ gemountet)
SETUP_SCRIPT_SOURCE = "/root/setup.py"

#<<<--------------------------------------------------------------DISK SELECTION------------------------------------------------------------>>>>

print("---------------Scanning available disks---------------------")
result = subprocess.run("lsblk -d -n -o NAME,SIZE,MODEL", shell=True, capture_output=True, text=True)
print(result.stdout)

Drive = input("Welches Laufwerk soll verwendet werden? (z.B. /dev/sda): ").strip()

if not Drive.startswith("/dev/"):
    Drive = f"/dev/{Drive}"

print(f"Selected drive: {Drive}")
print("---------------Disk selected---------------------")
print("\n"*2)

if "nvme" in Drive:
    boot_part = f"{Drive}p1"
    root_part = f"{Drive}p2"
else:
    boot_part = f"{Drive}1"
    root_part = f"{Drive}2"

#<<<--------------------------------------------------------------FUNCTIONS------------------------------------------------------------>>>>

def execute_command(command: str):
    subprocess.run(command, shell=True, timeout=Timeout, check=True)

def install_package(package: str):
    execute_command(f"pacman -S {package} --noconfirm")


def setup_base_system():
    print("---------------Configuring keyboard layout and timezone---------------------")
    execute_command(f"loadkeys {keyboard_layout}")
    execute_command(f"timedatectl set-timezone {timezone}")
    print("Keyboard layout: " + keyboard_layout)
    print("Timezone: " + timezone)
    print("---------------Keyboard layout and timezone configured---------------------")
    print("\n"*2)
    print("---------------Harddrive partitions---------------------")
    execute_command(f'sgdisk --clear --new=1:0:+1G --typecode=1:ef00 --change-name=1:"EFI" --new=2:0:0 --typecode=2:8300 --change-name=2:"ROOT" {Drive}')
    print("---------------Harddrive partitions configured---------------------")
    print("\n"*2)
    print("---------------Formatting partitions---------------------")
    execute_command(f"mkfs.vfat -F 32 {boot_part}")
    execute_command(f"mkfs.ext4 {root_part}")
    print("---------------Partitions formatted---------------------")
    print("\n"*2)
    print("---------------Mounting partitions---------------------")
    execute_command(f"mount {root_part} /mnt")
    execute_command(f"mkdir -p /mnt/boot")
    execute_command(f"mount {boot_part} /mnt/boot")
    print("---------------Partitions mounted---------------------")
    print("\n"*2)
    print("---------------Installing base system---------------------")
    execute_command("pacstrap -K /mnt base base-devel linux linux-firmware networkmanager nano sudo python git")
    print("---------------Base system installed---------------------")
    print("\n"*2)
    print("---------------Generating fstab---------------------")
    execute_command("genfstab -U /mnt >> /mnt/etc/fstab")
    print("---------------fstab generated---------------------")
    print("\n"*2)
    print("="*50)
    print("DONE WITH THE BASE SYSTEM SETUP")
    print("="*50)


def copy_setup_script():
    """
    Kopiert setup.py vom ISO (/root/setup.py) in das neue System
    nach /home/<profile_name>/setup.py.
    Ownership wird erst im chroot gesetzt, wenn der User existiert.
    """
    dest_dir  = f"/mnt/home/{profile_name}"
    dest_file = f"{dest_dir}/setup.py"

    print("---------------Copying setup.py to new system---------------------")

    if not os.path.exists(SETUP_SCRIPT_SOURCE):
        print(f"WARNING: {SETUP_SCRIPT_SOURCE} not found — setup.py wird NICHT kopiert.")
        return

    execute_command(f"mkdir -p {dest_dir}")
    execute_command(f"cp {SETUP_SCRIPT_SOURCE} {dest_file}")
    print(f"-> setup.py kopiert nach {dest_file}")


def install_autostart_service():
    """
    Legt einen Systemd-Oneshot-Service an, der setup.py beim ersten
    Boot automatisch als root ausfuehrt und sich danach selbst deaktiviert.
    """
    print("---------------Installing first-boot service---------------------")

    service_dir  = "/mnt/etc/systemd/system"
    service_path = f"{service_dir}/first-boot-setup.service"

    service_content = f"""[Unit]
Description=First-boot setup (install desktop environment)
After=network.target
ConditionPathExists=/home/{profile_name}/setup.py

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/{profile_name}/setup.py
ExecStartPost=/usr/bin/systemctl disable first-boot-setup.service
ExecStartPost=/usr/bin/rm -f /home/{profile_name}/setup.py
RemainAfterExit=no
StandardOutput=journal+console
StandardError=journal+console

[Install]
WantedBy=multi-user.target
"""

    os.makedirs(service_dir, exist_ok=True)
    with open(service_path, "w", newline="\n") as f:
        f.write(service_content)

    wants_dir = f"{service_dir}/multi-user.target.wants"
    execute_command(f"mkdir -p {wants_dir}")
    execute_command(
        f"ln -sf /etc/systemd/system/first-boot-setup.service "
        f"{wants_dir}/first-boot-setup.service"
    )

    print("-> first-boot-setup.service installiert und aktiviert.")


def configure_chroot():
    print("---------------Configuring chroot---------------------")
    chroot_script = f"""#!/bin/bash
set -ex

# Zeitzone
ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime
hwclock --systohc

# Sprachauswahl (Locales)
echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=de_DE.UTF-8" > /etc/locale.conf
echo "KEYMAP={keyboard_layout}" > /etc/vconsole.conf

# Hostname
echo "{system_name}" > /etc/hostname

# Root Passwort setzen
echo "root:{root_password}" | chpasswd

# User erstellen (nur wenn noch nicht vorhanden)
if ! id "{profile_name}" &>/dev/null; then
    useradd -m -G wheel -s /bin/bash {profile_name}
fi
echo "{profile_name}:{profile_password}" | chpasswd

# Ownership von setup.py setzen (User existiert jetzt)
chown {profile_name}:{profile_name} /home/{profile_name}/setup.py 2>/dev/null || true

# Sudo fuer wheel-Gruppe aktivieren
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers

# Netzwerk aktivieren
systemctl enable NetworkManager

# Keyring initialisieren
pacman-key --init
pacman-key --populate archlinux

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
    execute_command(f"arch-chroot /mnt /root/chroot_setup.sh")
    execute_command("rm /mnt/root/chroot_setup.sh")
    print("---------------Chroot configured---------------------")
    print("\n"*2)
    print("="*50)
    print("DONE WITH THE CHROOT CONFIGURATION")
    print("="*50)
    print("\n"*2)


def finalize_installation():
    print("\n---------------Cleaning up and unmounting partitions---------------------")
    execute_command("umount -R /mnt")
    print("---------------Installation entirely complete!---------------------")
    print("\n"*2)
    print("You can now safely type 'reboot' to restart your PC.")
    print("Fortschritt von setup.py verfolgen: journalctl -u first-boot-setup.service -f")
    print("\n"*2)


#<<<--------------------------------------------------------------MAIN------------------------------------------------------------>>>>

if __name__ == "__main__":
    setup_base_system()
    copy_setup_script()          # NEU: setup.py rueberkopieren
    install_autostart_service()  # NEU: Systemd-Service anlegen
    configure_chroot()           # chroot (setzt auch Ownership von setup.py)
    finalize_installation()