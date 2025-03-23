import wmi
from QuocTan.NTFS import *

SECTOR_SIZE = 512


class Partition:
    def __init__(self, description_in_mbr):
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

        self.starting_byte = self.starting_sector * SECTOR_SIZE

    def __str__(self):
        return f"Status: {self.status}\nType: {self.type}\nNumber of sectors: {self.number_of_sectors}\nStarting sector: {self.starting_sector}\nStarting byte: {self.starting_byte}"
        
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
    partition.append(Partition(par))
    print(f"Partition {i+1}")
    print(partition[i])
    print()
bootsignature = fin.read(2)
fin.close()
