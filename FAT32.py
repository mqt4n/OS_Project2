from enum import Flag, auto 
from datetime import datetime 
import re 

class FAT:
	def __init__(self, data):
		self.data = data 
		self.elements = [] 

	def getClustersChain(self, startIndex):
		for i in range(0, len(self.data), 4):
			self.elements.append(int.from_bytes(self.data[i:i + 4], 'little'))
		
		clusterList = [] 
		while True:
			clusterList.append(startIndex)
			startIndex = self.elements[startIndex] 
			""" 0x0FFFFFFF: EOF | 0x0FFFFFF7: Bad Cluster"""
			if startIndex == 0x0FFFFFFF or startIndex == 0x0FFFFFF7:
				return clusterList
			
class Attribute(Flag):
		READ_ONLY = 1      # 0b00000001
		HIDDEN = 2         # 0b00000010
		SYSTEM = 4         # 0b00000100
		VOLLABEL = 8       # 0b00001000
		DIRECTORY = 16     # 0b00010000
		ARCHIVE = 32       # 0b00100000

class ENTRY:
	def __init__(self, data):
		self.data = data
		self.name = '' 
		num = int.from_bytes(self.data[0xB:0xC], byteorder='little')
		self.parseEntry()
	
	def parseEntry(self):
		self.is_subEntry = self.data[0xB:0xC] == b'\x0f' 
		self.is_delete = self.data[0] == 0xe5
		self.is_empty = self.data[0] == 0x00 
		self.is_label = Attribute.VOLLABEL in Attribute(int.from_bytes(self.data[0xB:0xC], byteorder='little'))

		if not self.is_subEntry:
			self.name = self.data[0x00:0x8]
			self.extension = self.data[0x8:0xB] 
			
			if self.is_delete or self.is_empty:
				self.name = "" 
				return 
			
			self.attribute = Attribute(int.from_bytes(self.data[0xB:0xC], byteorder='little'))
			if Attribute.VOLLABEL in self.attribute:
				self.is_label = True 
				return 
			
			self.dataTime() 

			# cluster start and size of archive 
			self.startClusterBytes = self.data[0x14:0x16][::-1] + self.data[0x1A:0x1C][::-1] 

			self.startCluster = int.from_bytes(self.startClusterBytes, byteorder='big')

			self.sizeOfArchive = int.from_bytes(self.data[0x1C:0x20], byteorder='little')
		
		else:
			name = b""
			for i in range(0x1, 0xB):
				name += int.to_bytes(self.data[i], 1, byteorder='little')
				if name.endswith(b"\xff\xff"):
					name = name[:-2]
					break
			
			for i in range(0xE, 0x1A):
				name += int.to_bytes(self.data[i], 1, byteorder='little')
				if name.endswith(b"\xff\xff"):
					name = name[:-2]
					break
			
			for i in range(0x1C, 0x20):
				name += int.to_bytes(self.data[i], 1, byteorder='little')
				if name.endswith(b"\xff\xff"):
					name = name[:-2]
					break
			
			self.name = name.decode('utf-16le').strip('\x00')
		
	def is_directory(self):
		return Attribute.DIRECTORY in self.attribute
	
	def is_archive(self):
		return Attribute.ARCHIVE in self.attribute
	
	def is_active_entry(self):
		return not (self.is_empty or self.is_subEntry or self.is_delete or self.is_label or Attribute.SYSTEM in self.attribute) 
			
	
	def dataTime(self):
		self.timeDataCreated = int.from_bytes(self.data[0xD:0x10], byteorder='little')
		self.dateDateCreated = int.from_bytes(self.data[0x10:0x12], byteorder='little')
		self.datelastAccessed = int.from_bytes(self.data[0x12:0x14], byteorder='little')
		self.timeUpdate = int.from_bytes(self.data[0x16:0x18], byteorder='little')
		self.Update = int.from_bytes(self.data[0x18:0x1A], byteorder='little')

		h = (self.timeDataCreated & 0b111110000000000000000000) >> 19
		m = (self.timeDataCreated & 0b000001111110000000000000) >> 13
		s = (self.timeDataCreated & 0b000000000001111110000000) >> 7
		ms =(self.timeDataCreated & 0b000000000000000001111111)
		year = 1980 + ((self.dateDateCreated & 0b1111111000000000) >> 9)
		mon = (self.dateDateCreated & 0b0000000111100000) >> 5
		day = self.dateDateCreated & 0b0000000000011111

		dateCreated_dt = datetime(year, mon, day, h, m, s)
		self.dateCreated = dateCreated_dt.strftime("%A, %B %d, %Y, %I:%M:%S %p")

		year = 1980 + ((self.datelastAccessed & 0b1111111000000000) >> 9)
		mon = (self.datelastAccessed & 0b0000000111100000) >> 5
		day = self.datelastAccessed & 0b0000000000011111

		self.lastAccessed = datetime(year, mon, day)

		h = (self.timeUpdate & 0b1111100000000000) >> 11
		m = (self.timeUpdate & 0b0000011111100000) >> 5
		s = (self.timeUpdate & 0b0000000000011111) * 2
		year = 1980 + ((self.Update & 0b1111111000000000) >> 9)
		mon = (self.Update & 0b0000000111100000) >> 5
		day = self.Update & 0b0000000000011111

		self.dateUpdate_dt = datetime(year, mon, day, h, m, s)
		self.dateUpdate = dateCreated_dt.strftime("%A, %B %d, %Y, %I:%M:%S %p")


class RDET:
	def __init__(self, data):
		self.data = data
		self.entries: list[ENTRY] = [] 
		self.entries = self.getEntryName() 
	
	def getEntryName(self):
		name = ''
		entries: list[ENTRY] = [] 
		cnt = 0
		for i in range(0, len(self.data), 32):
			cnt += 1
			entries.append(ENTRY(self.data[i: i + 32])) 
			if entries[-1].is_empty or entries[-1].is_delete:
				name = "" 
				continue
			elif entries[-1].is_subEntry:
				name = entries[-1].name + name 
				continue

			if name != '':
				entries[-1].name = name
			else:
				extension = entries[-1].extension.strip().decode() 
				if extension != '':
					entries[-1].name = entries[-1].name.strip().decode() + '.' + extension
				else:
					entries[-1].name = entries[-1].name.strip().decode()
			name = ''
		return entries 
	
	def getActiveEntries(self):
		entries = [] 
		for i in range(len(self.entries)):
			if self.entries[i].is_active_entry():
				entries.append(self.entries[i])
		
		return entries
	
	def findEntry(self, name):
		for i in range(len(self.entries)):
			if self.entries[i].name.lower() == name.lower() and self.entries[i].is_active_entry():
				return self.entries[i]
		
		return None 

class FAT32: 
	def __init__(self, sector_starting, usb) -> None:
		self.sectorStarting = sector_starting
		self.cwd =[]
		self.usb = usb
		self.fin = open(self.usb.DeviceID, "rb") 
		self.fin.seek(sector_starting * 512) 
		self.data = self.fin.read(512) 
		self.bootSector = {} 
		self.getDataBootSector() 
		self.bootSector['FAT Name'] = self.bootSector['FAT Name'].decode()
		self.bytePerSector = self.bootSector['Bytes per Sector'] 
		self.sectorPerCluster = self.bootSector['Sectors per Cluster']
		self.reservedSectors = self.bootSector['Reserved Sectors']
		self.numberOfFat = self.bootSector['Number of FATs']
		self.sectorInVolume = self.bootSector['Sectors In Volume']
		self.sectorPerFat = self.bootSector['Sectors Per FAT']
		self.startClusterRDET = self.bootSector['Starting Cluster of RDET'] 
		self.startSectorData = self.bootSector['Starting Sector of Data'] 

		# Read FAT
		self.fin.seek((self.sectorStarting + self.reservedSectors) * self.bytePerSector)

		fatSize = self.bytePerSector * self.sectorPerFat
		# Number of fat 
		self.FATList: list[FAT] = [] 
		for _ in range(self.numberOfFat):
			self.FATList.append(FAT(self.fin.read(fatSize)))

		# read RDET 
		clusterIndex = self.bootSector['Starting Cluster of RDET']
		self.RDET = RDET(self.getClusterS(clusterIndex)) 
		self.DET = {} 
		# DET stores information about subfolders, unlike RDET which only manages entries in the root directory.
		self.DET[clusterIndex] = self.RDET

		for item in self.RDET.entries:
			if item.is_label and not item.is_subEntry:
				self.volume = item.name


	def getDataBootSector(self):
		self.bootSector['Bytes per Sector'] = int.from_bytes(self.data[0xB:0xD], 'little')
		self.bootSector['Sectors per Cluster'] = int.from_bytes(self.data[0xD: 0xE], 'little')
		self.bootSector['Reserved Sectors'] = int.from_bytes(self.data[0xE:0x10], 'little')
		self.bootSector['Number of FATs'] = int.from_bytes(self.data[0x10:0x11], 'little')
		self.bootSector['Sectors In Volume'] = int.from_bytes(self.data[0x20:0x24], 'little')
		self.bootSector['Sectors Per FAT'] = int.from_bytes(self.data[0x24:0x28], 'little')
		self.bootSector['Starting Cluster of RDET'] = int.from_bytes(self.data[0x2C:0x30], 'little')
		self.bootSector['FAT Name'] = self.data[0x52:0x59]
		self.bootSector['Starting Sector of Data'] = self.bootSector['Reserved Sectors'] + self.bootSector['Number of FATs'] * self.bootSector['Sectors Per FAT']

	def clusterToSectorIndex(self, index):
		return self.numberOfFat * self.sectorPerFat + self.reservedSectors + (index - 2) * self.sectorPerCluster
	
	def getClusterS(self, index): 
		clusterList = self.FATList[0].getClustersChain(index)
		data = b"" 

		for i in clusterList:
			sectorIndex = self.clusterToSectorIndex(i)
			# first sector do not stored data => skip them 
			self.fin.seek((sectorIndex + self.sectorStarting) * self.bytePerSector) 
			data += self.fin.read(self.bytePerSector * self.sectorPerCluster)
		return data  
	
	def isFAT32(self):
		fat_name = self.bootSector.get("FAT Name", "").strip().upper()
		return "FAT32" == fat_name
		
		
	"""READ FILE"""

	def parsePath(self, path):
		dirs = re.sub(r"[/\\]+", r"\\", path).strip("\\").split("\\")
		return dirs
	

	def visitDirectory(self, path):
		if path == "": raise Exception("Require a directory")
		path = self.parsePath(path) 

		if path[0] == self.volume:
			# CDET = self.DET[self.bootSector["Starting Cluster of RDET"]]
			path.pop(0) 
		CDET = self.RDET
		
		for dir in path:
			entry = CDET.findEntry(dir) 
			if entry is None:
				raise Exception("Directory not found")
			if entry.is_directory():
				if entry.startCluster == 0:
					CDET = self.DET[self.bootSector["Starting Cluster of RDET"]] 
					continue
				if entry.startCluster in self.DET:
					CDET = self.DET[entry.startCluster]
					continue

				self.DET[entry.startCluster] = RDET(self.getClusterS(entry.startCluster))
				CDET = self.DET[entry.startCluster]
			else:
				raise Exception("Not a directory")

		return CDET 
	
	def getCWD(self):
		if len(self.cwd) == 1:
			return self.cwd[0] + "\\"
		return "\\".join(self.cwd) 
	
	def getDirectory(self, path = ""):
		try:
			ret = []
			if path != "":
				CDET = self.visitDirectory(path) 
				entryList = CDET.getActiveEntries()
			else:
				entryList = self.RDET.getActiveEntries() 
			for entry in entryList:
				obj = {}
				obj["ID"] = ""
				obj["Flags"] = entry.attribute.value
				obj["Date Created"] = entry.dateCreated
				obj["Date Modified"] = entry.dateUpdate
				obj["Size"] = entry.sizeOfArchive 
				obj["Name"] = entry.name 
				obj["Path"] = ""
				obj["Parent"] = self.volume
				obj["content"] = ""
				obj["Attribute"] =  [attr.name for attr in Attribute if attr in entry.attribute]

				if entry.startCluster == 0:
					obj["sector"] = (entry.startCluster + 2) * self.sectorPerCluster
				else:
					obj["sector"] = (entry.startCluster) * self.sectorPerCluster
				ret.append(obj)
			return ret
		except Exception as error:
			raise(error)

	
	def getText(self, path):
		parts = self.parsePath(path) 

		if len(parts) > 1:
			volume = parts[-1] 
			directoryPath = "\\".join(parts[:-1])
			CDET = self.visitDirectory(directoryPath)
			entry = CDET.findEntry(volume)
		else:
			entry = self.RDET.findEntry(parts[0])
		
		if entry is None:
			raise Exception("File do not exist")
		if entry.is_directory():
			raise Exception("Is Directory")
		
		if entry.extension.decode() != "TXT": return ""

		str = ""
		size = entry.sizeOfArchive
		ind = 0
		if size > 0: 
			ind = self.FATList[0].getClustersChain(entry.startCluster)
			for i in ind:
				if size <= 0: break
				offset = self.clusterToSectorIndex(i) 
				self.fin.seek((offset + self.sectorStarting) * self.bytePerSector)
				rawData = self.fin.read(min(self.sectorPerCluster * self.bytePerSector, size))
				size -= self.sectorPerCluster * self.bytePerSector

				try:
					str += rawData.decode()
				except Exception as e:
					raise e
		return str 

	def applyGUI(self, num):
		entries = []
		stored = []

		obj = {
			"ID": "FAT32_" + str(num),
			"Flags": 16, 
			"Date Created": None,
			"Date Modified": None, 
			"Size": 0,
			"Name": self.volume,
			"Path": "",
			"Parent": None,
			"content": "",
			"Attribute": None
		}
		num += 1

		entries.append(obj)
		stored.append(obj) 

		while len(stored) != 0:
			entry = stored.pop(0)
			entry["ID"] = "FAT32_" + str(num)
			num += 1
			
			if entry["Path"] == "":
				entry["Path"] = entry["Name"]
			else:
				entry["Path"] += "//" + entry["Name"]
			
			if entry["Flags"] == 16:
				for item in self.getDirectory(entry["Path"]):
					if item["Name"] not in [".", ".."]:
						item["Parent"] = entry["ID"]
						entries.append(item)
						stored.append(item) 
						item["Path"] = entry["Path"]
			elif entry["Flags"] == 32:
				entry["content"] = self.getText(entry["Path"])

		return num, entries

				