import wmi
from NTFS import *
from FAT32 import FAT32
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

arr = ["FAT32", "NTFS"]
for i in range(len(arr)): print(f"{i + 1} {arr[i]}")
print()
choise = int(input("Which option you choise: " ))
print()

res = arr[choise - 1]
for i in range(4):
    par = fin.read(16)
    partition.append(Partition(par, usb.DeviceID))
    if res == partition[i].type and res == "FAT32":
        
        main = FAT32("E:", partition[i].starting_sector)
        for item in main.getDirectory():
            print(item["Name"])

    elif res == partition[i].type and res == "NTFS":

        main = NTFS(partition[i])
        main.print_info_file()
    
fin.close()
