# Les dépendances pour compiler

sudo apt update
sudo apt install -y build-essential bc bison flex libssl-dev libelf-dev \
  libncurses-dev dwarves pahole pkg-config rsync wget debhelper dh-sequence-dkms fakeroot


# Récupération des sources

mkdir -p ~/kernel/6.14 && cd ~/kernel/6.14
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.14.5.tar.xz
tar -xf linux-6.14.5.tar.xz
cd linux-6.14.5

# Générer la configuration par défaut

make x86_64_defconfig

# Personnaliser son noyau

make menuconfig

## VirtIO / PCI

- CONFIG_VIRTIO=y
- CONFIG_VIRTIO_PCI=y
- CONFIG_VIRTIO_PCI_LEGACY=y (par sécurité, selon machine type QEMU)
- CONFIG_VIRTIO_PCI_MODERN=y

## Réseau virtio
CONFIG_VIRTIO_NET=y
CONFIG_INET=y

## Disque virtio

- CONFIG_VIRTIO_BLK=y

## Stockage + rootfs

- CONFIG_BLK_DEV_INITRD=y (garde initramfs, simplifie tout)
- CONFIG_EXT4_FS=y

## LVM / device-mapper
- CONFIG_MD=y
- CONFIG_BLK_DEV_DM=y
- CONFIG_DM_CRYPT peut rester n si pas de chiffrement
- CONFIG_DM_SNAPSHOT optionnel
- CONFIG_DM_MIRROR optionnel
- CONFIG_DM_THIN_PROVISIONING optionnel

## Console série (recommandé en VM)
- CONFIG_SERIAL_8250=y
- CONFIG_SERIAL_8250_CONSOLE=y

## Désactiver ce qui est inutile en VM

- Dans menuconfig, tu peux couper :
- GPU/DRM (si pas besoin d’affichage) : Device Drivers → Graphics support → désactive DRM
- Wi-Fi, Bluetooth
- Son
- FireWire, TV, etc.
- Beaucoup de drivers NIC physiques (tu gardes virtio_net)

## Configuration minimal du Réseau
- CONFIG_INET=y
- IPv6 optionnel
- Netfilter optionnel (dà ésactiver si on veux ultra-minimal)

## Option nécessaire pour eBPF (General setup)
- CONFIG_BPF=y
- CONFIG_BPF_SYSCALL=y
- CONFIG_BPF_JIT=y
- CONFIG_DEBUG_INFO_BTF=y (recommandé pour CO-RE)
- Tracing utile : CONFIG_FTRACE=y, CONFIG_KPROBES=y, CONFIG_UPROBES=y


## Loop + squashfs (indispensable pour snap)
- CONFIG_BLK_DEV_LOOP=y (ou m, mais alors il faut que le module soit dispo dans initramfs)
- CONFIG_SQUASHFS=y (ou m)
- CONFIG_SQUASHFS_XZ=y (core snaps sont souvent compressés en xz)
- CONFIG_SQUASHFS_ZLIB=y (utile aussi)
- (optionnel) CONFIG_SQUASHFS_LZO, CONFIG_SQUASHFS_LZ4

## Aide au montage

- CONFIG_DEVTMPFS=y
- CONFIG_DEVTMPFS_MOUNT=y

# Build and install

make -j"$(nproc)" bindeb-pkg LOCALVERSION=-kvmmin

cd ..

sudo dpkg -i linux-image-6.14.5-kvmmin_*_amd64.deb linux-headers-6.14.5-kvmmin_*_amd64.deb


## disable multipathd && snapd

sudo systemctl disable --now multipathd
sudo systemctl disable --now snapd.service snapd.socket snapd.seeded.service
sudo systemctl mask snapd.service snapd.socket snapd.seeded.service
#systemctl status multipathd --no-pager


sudo update-initramfs -c -k 6.14.5-kvmmin
sudo update-grub
sudo reboot 


