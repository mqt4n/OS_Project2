from datetime import datetime
SECTOR_SIZE = 512
WIN_EPOCH = 116444736000000000

def get_total_size(entry, list_file, volume_name):
    total_size = 0
    if entry.is_folder():
        for child in list_file:
            if entry.get_id() == child.get_parent_id():
                total_size += get_total_size(child, list_file, volume_name)
    else:
        total_size += entry.get_size()
    return total_size

def get_parent_name(parent_id, list_file, volume_name):
    for entry in list_file:
        if parent_id == 5:
            return volume_name
        if parent_id == entry.get_id():
            return entry.get_file_name()
    return None
        
def get_infomation(entry, list_file, volume_name, counter, total_sectors):
    return {
        "ID": str(counter)+"NTFS"+str(entry.get_id()),
        "Name": entry.get_file_name(),
        "Is Folder": entry.is_folder(),
        "Parent ID": str(counter)+"NTFS"+str(entry.get_parent_id()),
        "Size": get_total_size(entry, list_file, volume_name),
        "Create Time": entry.get_create_time(),
        "Modify Time": entry.get_modify_time(),
        "Data": entry.get_data(),
        "Attribute": entry.get_attributes(),
        "Total Size": total_sectors,
    }

class Partition:
    def __init__(self, description_in_mbr, location_of_disk, relative_starting_sector):
        self.status = (
            "bootable"
            if description_in_mbr[0] == 0x80
            else ("non-bootable" if description_in_mbr[0] == 0x00 
            else "unknown")
        )
        self.type = (
            "FAT32"
            if description_in_mbr[4] == 0x0C
            else ("NTFS" if description_in_mbr[4] == 0x07
            else ("EBR" if description_in_mbr[4] == 0x05
            else "unknown"))
        )
        self.number_of_sectors = int.from_bytes(description_in_mbr[12:16], "little")
        self.starting_sector = relative_starting_sector+int.from_bytes(description_in_mbr[8:12], "little")
        self.location_of_disk = location_of_disk

class EBR:
    def __init__(self,general_information: Partition):
        self.partition = general_information
        self.base_extended = self.partition.starting_sector
        self.list_of_partition = []
        self.read_extended_partition()
        
    def read_extended_partition(self):
        curLBA = 0
        while True:
            filein = open(self.partition.location_of_disk, "rb")
            filein.seek((self.base_extended + curLBA) * SECTOR_SIZE)
            partition_bytes = filein.read(512)
            partition_extend = partition_bytes[446:462]
            next_ebr = partition_bytes[462:478]
            filein.close()
            p = Partition(partition_extend, self.partition.location_of_disk, self.base_extended + curLBA)
            self.list_of_partition.append(p)
            if next_ebr == b'\x00' * 16:
                break
            curLBA = int.from_bytes(next_ebr[8:12], "little")
    
    def get_list_of_partition(self):
        return self.list_of_partition

class NTFS:
    counter = 0
    def __init__(self, general_information: Partition):
        NTFS.counter += 1
        self.partition = general_information
        self.start_partition = self.partition.starting_sector * SECTOR_SIZE
        self.volume_boot_record = NTFS_Volume_Boot_Record(
            self.start_partition,
            self.partition.location_of_disk,
        )
        self.bytes_per_cluster = (
            self.volume_boot_record.number_of_bytes_per_sector
            * self.volume_boot_record.number_of_sectors_per_cluster
        )
        self.master_file_table = []
        self.list_file = []
        self.read_master_file_table()
        self.nodes = {}

    def read_master_file_table(self):
        fin = open(self.partition.location_of_disk, "rb")
        start_bytes = (
            self.partition.starting_sector * SECTOR_SIZE
            + self.volume_boot_record.starting_cluster_of_mft
            * self.volume_boot_record.number_of_bytes_per_sector
            * self.volume_boot_record.number_of_sectors_per_cluster
        )
        fin.seek(start_bytes)
        number_of_entries = 1
        while number_of_entries:
            number_of_entries -= 1
            entry_bytes = fin.read(
                self.volume_boot_record.number_of_bytes_per_entry_in_mft
            )
            if entry_bytes[0] == 0:
                continue
            entry = NTFS_Master_File_Table_Entry(
                entry_bytes,
                self.bytes_per_cluster,
                self.partition.location_of_disk,
                self.start_partition,
            )
            if entry.get_file_name() == "$MFT":
                number_of_entries = (
                    entry.get_size()
                    // self.volume_boot_record.number_of_bytes_per_entry_in_mft
                    - 1
                )
            if entry.get_file_name() == "$Volume":
                self.volume_name = entry.attributes["VolumeName"].volume_name

            if not entry.is_deleted() and entry.get_file_name() != None:
                self.list_file.append(
                    (entry.get_id(), entry.get_parent_id(), entry.get_file_name())
                )
                self.master_file_table.append(entry)
        self.list_file.append((5,None, self.volume_name))  # Add root node
        fin.close()
            
    def get_list_file(self):
        tmp = []
        tmp.append(
            {
                "ID": str(NTFS.counter)+"NTFS"+str(5),
                "Name": self.volume_name,
                "Is Folder": True,
                "Parent ID": None,
                "Size": None,
                "Create Time": None,
                "Modify Time": None,
                "Data": None,
                "Attribute": None,
                "Total Size": self.volume_boot_record.total_sectors*512,
            }
        )
        for entry in self.master_file_table:
            if entry.check_file():
                tmp.append(get_infomation(entry, self.master_file_table, self.volume_name, NTFS.counter, self.volume_boot_record.total_sectors*512))
        return tmp

class NTFS_Volume_Boot_Record:
    def __init__(self, starting_byte, location_of_disk):
        fin = open(location_of_disk, "rb")
        fin.seek(starting_byte)
        vbr_bytes = fin.read(512)
        self.number_of_bytes_per_sector = int.from_bytes(vbr_bytes[11:13], "little")
        self.number_of_sectors_per_cluster = int.from_bytes(vbr_bytes[13:14], "little")
        self.number_of_sectors_per_track = int.from_bytes(vbr_bytes[24:26], "little")
        self.number_of_heads = int.from_bytes(vbr_bytes[26:28], "little")
        self.total_sectors = int.from_bytes(vbr_bytes[40:48], "little")
        self.starting_cluster_of_mft = int.from_bytes(vbr_bytes[48:56], "little")
        self.starting_cluster_of_mft_mirror = int.from_bytes(vbr_bytes[56:64], "little")
        tmp = int.from_bytes(vbr_bytes[64:65], "little", signed=True)
        self.number_of_bytes_per_entry_in_mft = 2 ** abs(tmp) if tmp < 0 else tmp
        fin.close()

class Atribute_Standard_Information:
    def convert_nano_second(self, byte):
        nano_second = int.from_bytes(byte, "little")
        timestamp_seconds = (nano_second - WIN_EPOCH) // 10000000
        date = datetime.fromtimestamp(timestamp_seconds)
        date_formatted = date.strftime("%A, %B %d, %Y, %I:%M:%S %p")
        return str(date_formatted)

    def __init__(self, SI_bytes):
        self.create_time = self.convert_nano_second(SI_bytes[0:8])
        self.modify_time = self.convert_nano_second(SI_bytes[8:16])
        self.mft_modify_time = self.convert_nano_second(SI_bytes[16:24])
        self.access_time = self.convert_nano_second(SI_bytes[24:32])

class Atribute_File_Name:
    def convert_flag(self, byte):
        flag = int.from_bytes(byte, "little")
        res = []
        if flag & 0x0001:
            res.append("Read Only")
        if flag & 0x0002:
            res.append("Hidden")
        if flag & 0x0004:
            res.append("System")
        if flag & 0x0020:
            res.append("Archive")
        if flag & 0x10000000:
            res.append("Directory")
        return res

    def __init__(self, FN_bytes):
        self.parent_id = int.from_bytes(FN_bytes[0:6], "little")
        self.flag = self.convert_flag(FN_bytes[56:60])
        self.length_of_name = int.from_bytes(FN_bytes[64:65], "little")
        # 1 Character = 2 bytes
        self.name = FN_bytes[66 : 66 + self.length_of_name * 2].decode("utf-16le")
        self.extension = self.name.split(".")[-1] if "." in self.name else None

class Cluster_runlist:
    def __init__(self, runlist_bytes, bytes_per_cluster):
        self.bytes_per_cluster = bytes_per_cluster
        self.runlist_bytes = runlist_bytes
        self.runlist = []
        self.read_runlist()

    def read_runlist(self):
        rbytes = self.runlist_bytes
        real_offset = 0
        while True:
            header = int.from_bytes(rbytes[0:1], "little")
            if not header:
                break
            length_cluster = header & 0x0F
            offset_cluster = (header >> 4) & 0x0F
            length = int.from_bytes(rbytes[1 : 1 + length_cluster], "little")
            offset = int.from_bytes(
                rbytes[length_cluster+1 : 1 + length_cluster + offset_cluster],
                "little",
            )
            real_offset += offset
            self.runlist.append(
                (
                    length * self.bytes_per_cluster,
                    real_offset * self.bytes_per_cluster,
                )
            )
            rbytes = rbytes[1 + length_cluster + offset_cluster :]

    def get_runlist(self):
        return self.runlist

class Atribute_Data:
    def __init__(
        self,
        data_bytes,
        content_offset,
        content_size,
        resident,
        extension,
        bytes_per_cluster,
        location_of_disk,
        start_partition,
    ):
        if resident == 0:
            self.data_size = content_size
            if extension == "txt":
                try:
                    self.data = data_bytes[content_offset : content_offset + content_size].decode()
                except UnicodeDecodeError:
                    self.data = data_bytes[content_offset : content_offset + content_size].decode(errors='ignore')
                
        else:
            self.data_size = int.from_bytes(data_bytes[48:56], "little")
            if extension == "txt":
                offset_to_runlist = int.from_bytes(data_bytes[32:34], "little")
                name_length =  data_bytes[9]
                offset_to_runlist += name_length*2
                runlist_bytes = data_bytes[offset_to_runlist:]
                list_runlist = Cluster_runlist(runlist_bytes, bytes_per_cluster)
                self.data = ""
                total = self.data_size
                for length, offset in list_runlist.get_runlist():
                    fin = open(location_of_disk, "rb")
                    fin.seek(start_partition + offset)
                    if length > total:
                        length = total
                    else:
                        total -= length
                    tmp = fin.read(length)
                    try:
                        self.data += tmp.decode()
                    except UnicodeDecodeError:
                        self.data += tmp.decode(errors='ignore')
                    fin.close()

class Attribute_Volume_Name:
    def __init__(self, VN_bytes):
        self.volume_name = VN_bytes.decode("utf-16le")

class NTFS_Master_File_Table_Entry:
    def convert_attr_type(self, value):
        if value == 0x10:
            return "StandardInformation"
        elif value == 0x30:
            return "FileName"
        elif value == 0x80:
            return "Data"
        elif value == 0x60:
            return "VolumeName"
        elif value == 0xFFFFFFFF:
            return "End"
        return None

    def __init__(
        self, entry_bytes, bytes_per_cluster, location_of_disk, start_partition
    ):
        self.start_partition = start_partition
        self.location_of_disk = location_of_disk
        self.bytes_per_cluster = bytes_per_cluster
        self.signature = entry_bytes[0:4].decode("utf-8")
        self.starting_offset_of_first_attribute = int.from_bytes(
            entry_bytes[20:22], "little"
        )
        self.state = int.from_bytes(entry_bytes[22:24], "little")
        self.number_of_bytes_in_use = int.from_bytes(entry_bytes[24:28], "little")
        self.number_of_bytes_of_mft_entry = int.from_bytes(entry_bytes[28:32], "little")
        self.id_of_mft_entry = int.from_bytes(entry_bytes[44:48], "little")
        self.attributes = {}
        self.read_attributes(entry_bytes[self.starting_offset_of_first_attribute :])

    def read_attributes(self, attribute_bytes):
        while True:
            attribute_type = self.convert_attr_type(
                int.from_bytes(attribute_bytes[0:4], "little")
            )
            attribute_length = int.from_bytes(attribute_bytes[4:8], "little")
            resident = int.from_bytes(attribute_bytes[8:9], "little")
            content_size = 0
            content_offset = 0
            if resident == 0:
                content_size = int.from_bytes(attribute_bytes[16:20], "little")
                content_offset = int.from_bytes(attribute_bytes[20:22], "little")
            if attribute_type == "End":
                break
            elif attribute_type == "StandardInformation":
                self.attributes["StandardInformation"] = Atribute_Standard_Information(
                    attribute_bytes[content_offset : content_offset + content_size]
                )
            elif attribute_type == "FileName":
                self.attributes["FileName"] = Atribute_File_Name(
                    attribute_bytes[content_offset : content_offset + content_size]
                )
            elif attribute_type == "Data":
                self.attributes["Data"] = Atribute_Data(
                    attribute_bytes,
                    content_offset,
                    content_size,
                    resident,
                    self.get_extension(),
                    self.bytes_per_cluster,
                    self.location_of_disk,
                    self.start_partition,
                )
            elif attribute_type == "VolumeName":
                self.attributes["VolumeName"] = Attribute_Volume_Name(
                    attribute_bytes[content_offset : content_offset + content_size]
                )
            attribute_bytes = attribute_bytes[attribute_length:]

    def get_file_name(self):
        if "FileName" in self.attributes:
            return self.attributes["FileName"].name

    def get_size(self):
        if "Data" in self.attributes:
            return self.attributes["Data"].data_size

    def get_extension(self):
        if "FileName" in self.attributes:
            return self.attributes["FileName"].extension

    def is_folder(self):
        if "FileName" in self.attributes:
            return "Directory" in self.attributes["FileName"].flag
        
    def get_data(self):
        if "Data" in self.attributes:
            if self.get_extension() == "txt":
                return self.attributes["Data"].data
        return 0
    
    def get_parent_id(self):
        if "FileName" in self.attributes:
            return self.attributes["FileName"].parent_id

    def get_id(self):
        return self.id_of_mft_entry

    def check_file(self):
        list_attr = ["Read Only", "Hidden", "System"]
        if "FileName" in self.attributes:
            for attr in list_attr:
                if attr in self.attributes["FileName"].flag:
                    return False
        return True

    def get_create_time(self):
        if "StandardInformation" in self.attributes:
            return self.attributes["StandardInformation"].create_time
        
    def get_modify_time(self):
        if "StandardInformation" in self.attributes:
            return self.attributes["StandardInformation"].modify_time
    
    def is_deleted(self):
        if self.state == 0x00 or self.state == 0x02:
            return True
        return False
    
    def get_attributes(self):
        return self.attributes["FileName"].flag if "FileName" in self.attributes else None
    