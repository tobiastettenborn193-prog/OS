#<<<--------------------------------------------------------------IMPORTS------------------------------------------------------------>>>>
import subprocess
import sys
import os 

#<<<--------------------------------------------------------------HYPERPARAMETERS------------------------------------------------------------>>>>

#timeout
Timeout = 300

#system name
system_name = "Arch"
#profile name
profile_name = "tobster"
#profile password
profile_password = "1903"
#root password
root_password = "1903.Tt."
#keyboard layout
keyboard_layout = "de-latin1"
#timezone
timezone = "Europe/Berlin"
#DRIVE
Drive = "/dev/sda"


#Partitions
if "nvme" in Drive:
    boot_part = f"{Drive}p1"
    root_part = f"{Drive}p2"
else:
    boot_part = f"{Drive}1"
    root_part = f"{Drive}2"

#<<<--------------------------------------------------------------FUNCTIONS------------------------------------------------------------>>>>

##################################################BASIC FUNCTIONS################################################

##########Simple Function which executes a command
def execute_command(command: str):
    subprocess.run(command, shell=True, timeout=Timeout, check=True)

##########SIMPLE FUNCTION TO INSTALL STUFF IF NEEDED
def install_package(package: str):
    execute_command(f"pacman -S {package} --noconfirm")

#################################################INSTALLATION FUNCTIONS##############################################
"""Here starts the actual script for the installation, these functions are necessary for the installation process"""


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
    execute_command(f"pacstrap /mnt base base-devel linux linux-firmware networkmanager nano sudo python uv git --noconfirm")
    print("---------------Base system installed---------------------")
    print("\n"*2)
    print("---------------Generating fstab---------------------")
    execute_command("genfstab -U /mnt >> /mnt/etc/fstab")
    print("---------------fstab generated---------------------")
    print("\n"*2)
    print("="*50)
    print("DONE WITH THE BASE SYSTEM SETUP")
    print("="*50)

def configure_chroot():
    print("---------------Configuring chroot---------------------")
    chroot_script = f"""#!/bin/bash
set -e

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

# User erstellen
useradd -m -G wheel -s /bin/bash {profile_name}
echo "{profile_name}:{profile_password}" | chpasswd

# Sudo fuer wheel-Gruppe aktivieren
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers

# Netzwerk aktivieren
systemctl enable NetworkManager

# Bootloader (GRUB) installieren
pacman -S --noconfirm grub efibootmgr
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
"""
    
    chroot_script_path = "/mnt/tmp/chroot_setup.sh"
    with open(chroot_script_path, "w") as f:
        f.write(chroot_script)
        
    execute_command(f"chmod +x {chroot_script_path}")
    execute_command(f"arch-chroot /mnt /tmp/chroot_setup.sh")
    execute_command(f"rm {chroot_script_path}")
    print("---------------Chroot configured---------------------")
    print("\n"*2)
    print("="*50)
    print("DONE WITH THE CHROOT CONFIGURATION")
    print("="*50)
    print("\n"*2)

def finalize_installation():
    """
    Handles the transition into the newly installed system.
    Copies the setup script, opens an interactive chroot environment, 
    and securely unmounts the drives once the user is done.
    """
    print("---------------Copying setup script to the new system---------------------")
    
    execute_command("cp /root/setup.py /mnt/root/")
    
    print("\n" + "="*50)
    print("BASE SYSTEM INSTALLATION COMPLETE!")
    print("="*50 + "\n")
    
    print("\n---------------Cleaning up and unmounting partitions---------------------")
    execute_command("umount -R /mnt")
    
    print("---------------Installation entirely complete!---------------------")
    print("\n"*2)
    print("You can now safely type 'reboot' to restart your PC.")
    print("\n"*2)


#<<<--------------------------------------------------------------MAIN------------------------------------------------------------>>>>

if __name__ == "__main__":
    setup_base_system()
    configure_chroot()
    finalize_installation()
    print("---------------Installation complete!---------------------")
    print("\n"*2)
    print("You can now reboot and log in as root with the password you set")
    print("\n"*2)