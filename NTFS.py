from datetime import datetime

SECTOR_SIZE = 512
WIN_EPOCH = 116444736000000000

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

            if not entry.is_deleted() and entry.get_file_name() != None and entry.check_file():
                self.list_file.append(
                    (entry.get_id(), entry.get_parent_id(), entry.get_file_name())
                )
                self.master_file_table.append(entry)
        self.list_file.append((5,None, self.volume_name))  # Add root node
        fin.close()

    def build_tree(self):
        # First create all nodes
        for id, parent_id, name in self.list_file:
            self.nodes[id] = Node(id, self.volume_name if id == 5 else name)

        # Then build parent-child relationships
        for id, parent_id, name in self.list_file:
            if parent_id in self.nodes and parent_id != id:  # Prevent self-parenting
                self.nodes[parent_id].add_child(self.nodes[id])

        # Return the root node (assuming root has id=5)
        return self.nodes.get(5, None)

    def print_tree(self):
        root = self.build_tree()
        if root:
            root.print_tree()
        else:
            print("No root node found")
            
    def print_info_file(self):
        for entry in self.master_file_table:
            print(entry.get_info())
            print()

class Node:
    def __init__(self, my_id, name):
        self.id = my_id
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def get_id(self):
        return self.id

    def get_children(self):
        return self.children

    def print_tree(self, indent=0, parent_prefix=""):
        """Recursively prints the tree structure with proper indentation"""
        # Current line prefix
        if indent == 0:
            prefix = ""
        else:
            prefix = parent_prefix + ("└── " if self.is_last else "├── ")
        
        print(f"{prefix}{self.name}")

        # Prepare prefix for children
        if indent > 0:
            child_prefix = parent_prefix + ("    " if self.is_last else "│   ")
        else:
            child_prefix = ""

        # Print children
        for i, child in enumerate(self.children):
            child.is_last = (i == len(self.children) - 1)
            child.print_tree(indent + 1, child_prefix)

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
                    self.data = data_bytes[content_offset : content_offset + content_size].decode("utf-16le")
                
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
                        self.data += tmp.decode("utf-16le")
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

    def get_data(self):
        if "Data" in self.attributes:
            if self.get_extension() == "txt":
                return self.attributes["Data"].data

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

    def is_deleted(self):
        if self.state == 0x00 or self.state == 0x02:
            return True
        return False

    def get_info(self):
        data = self.get_data()
        strdata = f"Data:\n{data}" if data else ""
        if "FileName" in self.attributes:
            return (
                f"Name: {self.attributes['FileName'].name}\nAttributes: "
                + ", ".join(attr for attr in self.attributes["FileName"].flag)
                + "\n"
                + f"Create time: {self.attributes['StandardInformation'].create_time}\nModify time: {self.attributes['StandardInformation'].modify_time}\nSize: {self.get_size()} bytes\nExtension: {self.get_extension()}\n"
                + strdata
            )
