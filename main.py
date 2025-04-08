import os
import wmi
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import math
from helper.NTFS import *
from helper.FAT32 import *
SECTOR_SIZE = 512
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.aiff', '.alac', '.opus', '.amr', '.mid', '.midi'}
IMAGE_EXTENSIONS = {'.jpg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heif', '.svg', '.ico', '.raw'}
PDF_EXTENSIONS = {'.pdf'}
WORD_EXTENSIONS = {'.doc', '.docx', '.dot', '.dotx', '.docm', '.dotm'}
EXCEL_EXTENSIONS = {'.xls', '.xlsx', '.xlsm', '.xlsb', '.xltx', '.xltm'}
PPTX_EXTENSIONS = {'.pptx', '.pptm', '.potx', '.potm', '.ppsx', '.ppsm'}
TEXT_EXTENSIONS = {'.txt', '.csv', '.log', '.xml', '.json', '.html', '.htm', '.css', '.js'}
ZIP_EXTENSIONS = {'.zip', '.tar', '.gz', '.bz2', '.7z', '.xz', '.iso'}
RAR_EXTENSIONS = {'.rar'}
EXECUTABLE_EXTENSIONS = {'.exe', '.msi', '.bat', '.cmd', '.ps1', '.sh'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'}
CODE_EXTENSIONS = {'.py', '.java', '.cpp', '.c', '.h', '.js', '.php', '.html', '.css', '.json', '.xml'}


class Entry:
    def __init__(self, selfid, name, is_folder, parentID, size, created_date, modified_date, content, attributes, file_system, size_of_disk):
        self.id = selfid
        self.name = name
        self.is_folder = is_folder
        self.parentId = parentID
        self.size = size
        self.created_date = created_date
        self.modified_date = modified_date
        self.content = content
        self.attributes = attributes
        self.file_system = file_system
        self.size_of_disk = size_of_disk

class App:
    def __init__(self, root, entries):
        self.root = root
        self.root.title("[23127115 - 23127334] File Explorer")
        self.root.geometry("900x600")
        self.root.configure(bg="white")

        self.entries = entries
        self.entry_dict = {entry.id: entry for entry in entries}
        
        self.labels = {
            'name': None,
            'attributes': None,
            'created': None,
            'modified': None,
            'size': None
        }

        self.configure_style()
        self.load_icons()
        self.create_main_ui()
        self.initial()

    def configure_style(self):
        self.style = ttk.Style()
        self.root.tk_setPalette(background="#f7f9fc")

        self.style.configure("TFrame", background="#f7f9fc")
        self.style.configure("TLabel", background="#f7f9fc", foreground="#222", font=("Segoe UI", 10))
        self.style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#333", font=("Segoe UI", 10))
        self.style.map("Treeview", background=[("selected", "#d0e7ff")], foreground=[("selected", "#000")])
        
        self.style.configure("TNotebook", background="#f7f9fc", borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                            background="#e6f0ff", 
                            foreground="#222", 
                            padding=[12, 6], 
                            font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#cde5ff")])

        self.style.configure("TScrollbar", background="#d1e0ff", arrowcolor="#4da3ff")
        self.style.configure("TButton", font=("Segoe UI", 9), padding=6)
        self.style.map("TButton",
                      foreground=[("active", "#222"), ("!active", "#222")],
                      background=[("active", "#f7f9fc"), ("!active", "#f7f9fc")])

    def load_icons(self):
        # Load folder and partition icons (keep existing)
        expand_folder_img = Image.open("asset/expand_folder.png").resize((16, 16))
        collapse_folder_img = Image.open("asset/collapse_folder.png").resize((16, 16))
        file_img = Image.open("asset/file.png").resize((16, 16))
        ntfs_partition_img = Image.open("asset/ntfs_partition.png").resize((16, 16))
        fat32_partition_img = Image.open("asset/fat32_partition.png").resize((16, 16))
        refresh_img = Image.open("asset/refresh.png").resize((16, 16))
        
        # Load file type specific icons
        audio_img = Image.open("asset/audio.png").resize((16, 16))
        image_img = Image.open("asset/image.png").resize((16, 16))
        pdf_img = Image.open("asset/pdf.png").resize((16, 16))
        word_img = Image.open("asset/word.png").resize((16, 16))
        excel_img = Image.open("asset/excel.png").resize((16, 16))
        powerpoint_img = Image.open("asset/powerpoint.png").resize((16, 16))
        text_img = Image.open("asset/text.png").resize((16, 16))
        zip_img = Image.open("asset/zip.png").resize((16, 16))
        rar_img = Image.open("asset/rar.png").resize((16, 16))
        executable_img = Image.open("asset/executable.png").resize((16, 16))
        video_img = Image.open("asset/video.png").resize((16, 16))
        code_img = Image.open("asset/code.png").resize((16, 16))
        
        # Create PhotoImage objects
        self.expand_folder_icon = ImageTk.PhotoImage(expand_folder_img)
        self.collapse_folder_icon = ImageTk.PhotoImage(collapse_folder_img)
        self.file_icon = ImageTk.PhotoImage(file_img)
        self.ntfs_partition_icon = ImageTk.PhotoImage(ntfs_partition_img)
        self.fat32_partition_icon = ImageTk.PhotoImage(fat32_partition_img)
        self.refresh_icon = ImageTk.PhotoImage(refresh_img)
        
        # File type icons
        self.audio_icon = ImageTk.PhotoImage(audio_img)
        self.image_icon = ImageTk.PhotoImage(image_img)
        self.pdf_icon = ImageTk.PhotoImage(pdf_img)
        self.word_icon = ImageTk.PhotoImage(word_img)
        self.excel_icon = ImageTk.PhotoImage(excel_img)
        self.powerpoint_icon = ImageTk.PhotoImage(powerpoint_img)
        self.text_icon = ImageTk.PhotoImage(text_img)
        self.zip_icon = ImageTk.PhotoImage(zip_img)
        self.rar_icon = ImageTk.PhotoImage(rar_img)
        self.executable_icon = ImageTk.PhotoImage(executable_img)
        self.video_icon = ImageTk.PhotoImage(video_img)
        self.code_icon = ImageTk.PhotoImage(code_img)

    def create_main_ui(self):
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="white",
                                           sashwidth=5, sashrelief=tk.RAISED, sashpad=2, opaqueresize=False)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create tree frame with button at top
        self.tree_frame = tk.Frame(self.paned_window, bg="white", bd=2, relief=tk.GROOVE)
        
        # Add refresh button at top of tree frame
        self.refresh_btn = ttk.Button(
            self.tree_frame,
            image=self.refresh_icon,
            compound=tk.LEFT,
            text=" Refresh",
            command=self.refresh_data,
            style="TButton"
        )
        self.refresh_btn.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Add treeview below button
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        self.tree.bind("<<TreeviewOpen>>", self.on_folder_open)
        self.tree.bind("<<TreeviewClose>>", self.on_folder_close)
        self.tree.bind("<<TreeviewSelect>>", self.show_entry_info)

        self.detail_frame = tk.Frame(self.paned_window, bg="white", bd=2, relief=tk.GROOVE)
        self.notebook = ttk.Notebook(self.detail_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.info_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.info_tab, text="Information")
        
        self.labels['name'] = tk.Label(self.info_tab, text="", anchor='w', bg="white", font=("Segoe UI", 10))
        self.labels['attributes'] = tk.Label(self.info_tab, text="", anchor='w', bg="white", font=("Segoe UI", 10))
        self.labels['created'] = tk.Label(self.info_tab, text="", anchor='w', bg="white", font=("Segoe UI", 10))
        self.labels['modified'] = tk.Label(self.info_tab, text="", anchor='w', bg="white", font=("Segoe UI", 10))
        self.labels['size'] = tk.Label(self.info_tab, text="", anchor='w', bg="white", font=("Segoe UI", 10))
        
        for i, label in enumerate(self.labels.values()):
            label.grid(row=i, column=0, sticky='ew', padx=5, pady=2)

        self.content_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.content_tab, text="Content")
        self.content_text = scrolledtext.ScrolledText(
            self.content_tab,
            wrap=tk.WORD,
            state='disabled',
            bg="#ffffff",
            bd=1,
            relief=tk.GROOVE,
            font=("Consolas", 10),
            highlightbackground="#4da3ff",
            highlightthickness=1
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.paned_window.add(self.tree_frame)
        self.paned_window.add(self.detail_frame)

    def initial(self):
        for entry in self.entries:
            if entry.parentId is None:
                self.add_entry('', entry)

    def get_file_icon(self, filename):
        """Return the appropriate icon based on file extension"""
        _, ext = os.path.splitext(filename.lower())
        
        if ext in AUDIO_EXTENSIONS:
            return self.audio_icon
        elif ext in IMAGE_EXTENSIONS:
            return self.image_icon
        elif ext in PDF_EXTENSIONS:
            return self.pdf_icon
        elif ext in WORD_EXTENSIONS:
            return self.word_icon
        elif ext in EXCEL_EXTENSIONS    :
            return self.excel_icon
        elif ext in PPTX_EXTENSIONS:
            return self.powerpoint_icon
        elif ext in TEXT_EXTENSIONS:
            return self.text_icon
        elif ext in ZIP_EXTENSIONS:
            return self.zip_icon
        elif ext in RAR_EXTENSIONS:
            return self.rar_icon
        elif ext in EXECUTABLE_EXTENSIONS:
            return self.executable_icon
        elif ext in VIDEO_EXTENSIONS:
            return self.video_icon
        elif ext in CODE_EXTENSIONS:
            return self.code_icon
        else:
            return self.file_icon  # Default icon

    def add_entry(self, parent, entry):
        if entry.is_folder:
            # Check if folder has children
            has_children = any(subentry.parentId == entry.id for subentry in self.entries)
            
            if entry.attributes is None:  # This is a partition
                # Choose icon based on file system
                if entry.file_system == "NTFS":
                    icon = self.ntfs_partition_icon
                else:
                    icon = self.fat32_partition_icon
                
                item = self.tree.insert(parent, 'end', entry.id, text=f" {entry.name}",
                                      values=('partition',), image=icon)
            else:  # Regular folder
                item = self.tree.insert(parent, 'end', entry.id, text=f" {entry.name}",
                                      values=('folder',), image=self.collapse_folder_icon)
            
            # Only add dummy child if folder has children
            if has_children:
                self.tree.insert(item, 'end')
        else:
            # Get the appropriate icon based on file extension
            icon = self.get_file_icon(entry.name)
            self.tree.insert(parent, 'end', entry.id, text=f" {entry.name}",
                           values=('file',), image=icon)

    def on_folder_open(self, event):
        item = self.tree.focus()
        if not item:
            return

        entry = self.entry_dict.get(item)
        if not entry or not entry.is_folder:
            return

        # Change icon to expanded folder (only for regular folders, not partitions)
        if entry.attributes is not None:  # Regular folder
            self.tree.item(item, image=self.expand_folder_icon)

        # Check if this is the first time opening (has dummy child)
        children = self.tree.get_children(item)
        if len(children) == 1 and not self.tree.item(children[0], 'values'):
            # Remove dummy child
            self.tree.delete(children[0])
            
            # Add real children
            for subentry in self.entries:
                if subentry.parentId == entry.id:
                    self.add_entry(item, subentry)

    def on_folder_close(self, event):
        item = self.tree.focus()
        if not item:
            return

        entry = self.entry_dict.get(item)
        if not entry or not entry.is_folder:
            return

        # Change icon back to collapsed folder (only for regular folders, not partitions)
        if entry.attributes is not None:  # Regular folder
            self.tree.item(item, image=self.collapse_folder_icon)

    def show_entry_info(self, event=None):
        item = self.tree.focus()
        if not item:
            return

        entry = self.entry_dict.get(item)
        if not entry:
            return

        created = str(entry.created_date)
        modified = str(entry.modified_date)

        self.labels['name'].config(text=f"Name:           {entry.name}")
        strAttr = ""
        if entry.attributes is None:
            strAttr = entry.file_system
            self.labels['attributes'].config(text=f"File system:    {strAttr}")
            raw_size = format(entry.size_of_disk, ",") if entry.size_of_disk is not None else "N/A"
            self.labels['created'].config(text=f"Total size:      {self.format_size(entry.size_of_disk)} ({raw_size} Bytes)")
            self.labels['modified'].config(text="")
            self.labels['size'].config(text="")
        else:
            strAttr = " ".join(entry.attributes)
            self.labels['attributes'].config(text=f"Attribute:       {strAttr}")
            self.labels['created'].config(text=f"Created:        {created}")
            self.labels['modified'].config(text=f"Modified:      {modified}")
            raw_size = format(entry.size, ",") if entry.size is not None else "N/A"
            self.labels['size'].config(text=f"Total size:      {self.format_size(entry.size)} ({raw_size} Bytes)")

        # Clear content tab for folders and partitions
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        
        if not entry.is_folder:
            self.show_file_content(entry)
        else:
            # For folders/partitions, show a message instead of leaving empty
            self.content_text.insert(tk.END, f"This is a {'partition' if entry.attributes is None else 'folder'}.\nNo content to display.")
        
        self.content_text.config(state='disabled')
        self.notebook.select(self.info_tab)

    def show_file_content(self, entry):
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)

        if entry.content:
            self.content_text.insert(tk.END, entry.content)
        else:
            self.content_text.insert(tk.END, "")

        self.content_text.config(state='disabled')

    def format_size(self, size):
        if size is None:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{math.floor(size*100)/100} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def refresh_data(self):
        """Refresh the data and reload the UI"""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            new_entries = self.get_disk_data()
            self.entries = new_entries
            self.entry_dict = {entry.id: entry for entry in new_entries}
            
            self.initial()
            
            for label in self.labels.values():
                label.config(text="")
            self.content_text.config(state='normal')
            self.content_text.delete(1.0, tk.END)
            self.content_text.config(state='disabled')
            
            messagebox.showinfo("Refresh Complete", "Data has been refreshed successfully")
        except Exception as e:
            messagebox.showerror("Refresh Error", f"An error occurred while refreshing data:\n{str(e)}")

    def get_disk_data(self):
        """Function to get disk data (same as main logic)"""
        c = wmi.WMI()
        entries = []
        usb = None
        id_increase = 0

        for disk in c.Win32_DiskDrive():
            if disk.MediaType == "Removable Media":
                usb = disk

        fin = open(usb.DeviceID, "rb")
        fin.read(446)

        for i in range(4):
            par = fin.read(16)
            partition = Partition(par, usb.DeviceID, 0)
            if partition.type == "NTFS":
                main = NTFS(partition)
                list_file = main.get_list_file()

                for entry in list_file:
                    entries.append(
                        Entry(entry["ID"], entry["Name"], entry["Is Folder"],
                        entry["Parent ID"], entry["Size"], entry["Create Time"],
                        entry["Modify Time"], entry["Data"], entry["Attribute"], "NTFS",
                        partition.number_of_sectors * SECTOR_SIZE)
                        )
                    
            elif partition.type == "FAT32":
                main = FAT32(partition.starting_sector, usb)
                id_increase, arr = main.applyGUI(id_increase) 
                for item in arr:
                    entries.append(
                        Entry(item["ID"], item["Name"], item["Flags"] == 16, item["Parent"], item["Size"], 
                        item["Date Created"], item["Date Modified"], item["content"], item["Attribute"], 
                        "FAT32", partition.number_of_sectors * SECTOR_SIZE)
                        )
            elif partition.type == "EBR":
                ext = EBR(partition)
                list_partition = ext.get_list_of_partition()
                for p in list_partition:
                    if p.type == "NTFS":
                        main = NTFS(p)
                        list_file = main.get_list_file()
                        for entry in list_file:
                            entries.append(
                                Entry(entry["ID"], entry["Name"], entry["Is Folder"],
                                entry["Parent ID"], entry["Size"], entry["Create Time"],
                                entry["Modify Time"], entry["Data"], entry["Attribute"], "NTFS",
                                partition.number_of_sectors * SECTOR_SIZE)
                                )
                    elif p.type == "FAT32":
                        main = FAT32(p.starting_sector, usb)
                        id_increase, arr = main.applyGUI(id_increase) 
                        for item in arr:
                            entries.append(
                                Entry(item["ID"], item["Name"], item["Flags"] == 16, item["Parent"], item["Size"], 
                                item["Date Created"], item["Date Modified"], item["content"], item["Attribute"], 
                                "FAT32", partition.number_of_sectors * SECTOR_SIZE)
                                )
        fin.close()
        return entries

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root, [])
    
    new_entries = app.get_disk_data()
    app.entries = new_entries
    app.entry_dict = {entry.id: entry for entry in new_entries}
    app.initial()

    root.mainloop()