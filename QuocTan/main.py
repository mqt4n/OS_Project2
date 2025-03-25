import wmi
from NTFS import *

SECTOR_SIZE = 512


class Partition:
    def __init__(self, description_in_mbr, location_of_disk):
        self.status = (
            "bootable"
            if description_in_mbr[0] == 0x80
            else ("non-bootable" if description_in_mbr[0] == 0x00 else "unknown")
        )
        self.type = (
            "FAT32"
            if description_in_mbr[4] == 0x0C
            else ("NTFS" if description_in_mbr[4] == 0x07 else "unknown")
        )
        self.number_of_sectors = int.from_bytes(description_in_mbr[12:16], "little")
        self.starting_sector = int.from_bytes(description_in_mbr[8:12], "little")
        self.location_of_disk = location_of_disk

    def __str__(self):
        return f"Status: {self.status}\nType: {self.type}\nNumber of sectors: {self.number_of_sectors}\nStarting sector: {self.starting_sector}\n"


class NTFS:
    def __init__(self, general_information: Partition):
        self.partition = general_information
        self.volume_boot_record = NTFS_Volume_Boot_Record(
            self.partition.starting_sector * SECTOR_SIZE,
            self.partition.location_of_disk,
        )
        self.master_file_table = NTFS_Master_File_Table(
            self.partition.starting_sector * SECTOR_SIZE
            + self.volume_boot_record.starting_cluster_of_mft
            * self.volume_boot_record.number_of_bytes_per_sector
            * self.volume_boot_record.number_of_sectors_per_cluster,
            self.partition.location_of_disk,
        )

    def __str__(self):
        return f"{self.partition}{self.volume_boot_record}"


class NTFS_Volume_Boot_Record:
    def __init__(self, starting_byte, location_of_disk):
        fin = open(location_of_disk, "rb")
        fin.seek(starting_byte)
        tmp = fin.read(11)
        self.number_of_bytes_per_sector = int.from_bytes(fin.read(2), "little")
        self.number_of_sectors_per_cluster = int.from_bytes(fin.read(1), "little")
        tmp = fin.read(10)
        self.number_of_sectors_per_track = int.from_bytes(fin.read(2), "little")
        self.number_of_heads = int.from_bytes(fin.read(2), "little")
        tmp = fin.read(12)
        self.total_sectors = int.from_bytes(fin.read(8), "little")
        self.starting_cluster_of_mft = int.from_bytes(fin.read(8), "little")
        self.starting_cluster_of_mft_mirror = int.from_bytes(fin.read(8), "little")
        self.number_of_bytes_per_entry_in_mft = 2 ** abs(
            int.from_bytes(fin.read(1), "little", signed=True)
        )
        fin.close()

    def __str__(self):
        return f"Number of bytes per sector: {self.number_of_bytes_per_sector}\nNumber of sectors per cluster: {self.number_of_sectors_per_cluster}\nNumber of sectors per track: {self.number_of_sectors_per_track}\nNumber of heads: {self.number_of_heads}\nTotal sectors: {self.total_sectors}\nStarting cluster of MFT: {self.starting_cluster_of_mft}\nStarting cluster of MFT mirror: {self.starting_cluster_of_mft_mirror}\nNumber of bytes per entry in MFT: {self.number_of_bytes_per_entry_in_mft}\n"


class NTFS_Master_File_Table:
    def __init__(self, starting_bytes, location_of_disk):
        fin = open(location_of_disk, "rb")
        fin.seek(starting_bytes)
        self.signature = fin.read(4).decode("utf-8")
        print(self.signature)
        fin.close()


# Tạo đối tượng WMI
c = wmi.WMI()
usb = None
partition = []

# Lấy danh sách các ổ đĩa vật lý
for disk in c.Win32_DiskDrive():
    if disk.MediaType == "Removable Media":
        usb = disk

print(f"Caption: {usb.Caption}")
print(f"DeviceID: {usb.DeviceID}")
print()
fin = open(usb.DeviceID, "rb")
bootloader = fin.read(446)

for i in range(4):
    par = fin.read(16)
    partition.append(Partition(par, usb.DeviceID))
    if partition[i].type == "NTFS":
        partition[i] = NTFS(partition[i])
        print(partition[i])
fin.close()
