import wmi
from NTFS import *
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
        partition[i].print_tree()
        partition[i].print_info()
fin.close()
