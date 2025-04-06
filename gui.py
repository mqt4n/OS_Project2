import os
import wmi
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from PIL import Image, ImageTk
import math
from NTFS import *

# Class đại diện cho 1 mục (file hoặc thư mục)
class Entry:
    def __init__(self, selfid, name, is_folder, parentID, size, created_date, modified_date, content, attributes, file_system):
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

# Ứng dụng chính
class App:
    def __init__(self, root, entries):
        self.root = root
        self.root.title("[23127115 - 23127334] File Explorer")
        self.root.geometry("900x600")
        self.root.configure(bg="white")

        self.entries = entries
        self.entry_dict = {entry.id: entry for entry in entries}

        self.configure_style()
        self.load_icons()
        self.create_toolbar()
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
        self.style.configure("TNotebook.Tab", background="#e6f0ff", foreground="#222", padding=[12, 6], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#cde5ff")])

        self.style.configure("TScrollbar", background="#d1e0ff", arrowcolor="#4da3ff")


    def load_icons(self):
        folder_img = Image.open("asset/folder.png").resize((16, 16))
        file_img = Image.open("asset/file.png").resize((16, 16))
        partition_img = Image.open("asset/partition.png").resize((16, 16))
        self.folder_icon = ImageTk.PhotoImage(folder_img)
        self.file_icon = ImageTk.PhotoImage(file_img)
        self.partition_icon = ImageTk.PhotoImage(partition_img)
        

    def create_toolbar(self):
        self.toolbar = tk.Frame(self.root, bd=2, relief=tk.RIDGE, bg="#ffffff", highlightbackground="#e0e0e0", highlightthickness=1)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

    def create_main_ui(self):
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="white",
                                           sashwidth=5, sashrelief=tk.RAISED, sashpad=2, opaqueresize=False)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.tree_frame = tk.Frame(self.paned_window, width=300, bg="white", bd=2, relief=tk.GROOVE)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewOpen>>", self.click_folder)
        self.tree.bind("<<TreeviewSelect>>", self.show_entry_info)

        self.detail_frame = tk.Frame(self.paned_window, bg="white", bd=2, relief=tk.GROOVE)
        self.notebook = ttk.Notebook(self.detail_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.info_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.info_tab, text="Information")
        

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

    def add_entry(self, parent, entry):
        if entry.is_folder:
            if entry.attributes is None:
                item = self.tree.insert(parent, 'end', entry.id, text=f" {entry.name}",
                                        values=('partition',), image=self.partition_icon)
            else:
                item = self.tree.insert(parent, 'end', entry.id, text=f" {entry.name}",
                                        values=('folder',), image=self.folder_icon)
            self.tree.insert(item, 'end')
            self.tree.item(item, open=False)
        else:
            self.tree.insert(parent, 'end', entry.id, text=f" {entry.name}",
                             values=('file',), image=self.file_icon)

    def click_folder(self, event):
        item = self.tree.focus()
        if not item:
            return

        entry = self.entry_dict.get(item)
        if not entry or not entry.is_folder:
            return

        children = self.tree.get_children(item)
        for child in children:
            self.tree.delete(child)

        for subentry in self.entries:
            if subentry.parentId == entry.id:
                self.add_entry(item, subentry)

    def show_entry_info(self, event=None):
        self.labels = {
            'name': tk.Label(self.info_tab, text="Name: ", anchor='w', bg="white", font =("Segoe UI", 10)),
            'attributes': tk.Label(self.info_tab, text="Attributes:", anchor='w', bg="white", font =("Segoe UI", 10)),
            'created': tk.Label(self.info_tab, text="Created: ", anchor='w', bg="white", font =("Segoe UI", 10)),
            'modified': tk.Label(self.info_tab, text="Modified: ", anchor='w', bg="white", font =("Segoe UI", 10)),
            'size': tk.Label(self.info_tab, text="Total size: ", anchor='w', bg="white", font =("Segoe UI", 10)),
        }
        for i, label in enumerate(self.labels.values()):
            label.grid(row=i, column=0, sticky='ew', padx=5, pady=2)
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
            self.labels['created'].config(text=f"")
            self.labels['modified'].config(text=f"")
            self.labels['size'].config(text=f"")
        else:
            strAttr = " ".join(entry.attributes)

            self.labels['attributes'].config(text=f"Attribute:       {strAttr}")
            self.labels['created'].config(text=f"Created:        {created}")
            self.labels['modified'].config(text=f"Modified:      {modified}")
            raw_size = format(entry.size, ",") if entry.size is not None else "N/A"
            self.labels['size'].config(text=f"Total size:      {self.format_size(entry.size)} ({raw_size} Bytes)")

        if not entry.is_folder:
            self.show_file_content(entry)

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

if __name__ == "__main__":
    c = wmi.WMI()
    partition = []
    entries = []

    for disk in c.Win32_DiskDrive():
        if disk.MediaType == "Removable Media":
            usb = disk

    fin = open(usb.DeviceID, "rb")
    fin.read(446)

    for i in range(4):
        par = fin.read(16)
        partition.append(Partition(par, usb.DeviceID))
        if partition[i].type == "NTFS":
            main = NTFS(partition[i])
            list_file = main.get_list_file()

            for entry in list_file:
                entries.append(Entry(entry["ID"], entry["Name"], entry["Is Folder"],
                                     entry["Parent ID"], entry["Size"], entry["Create Time"],
                                     entry["Modify Time"], entry["Data"], entry["Attribute"], "NTFS"))

    fin.close()

    root = tk.Tk()
    app = App(root, entries)
    root.mainloop()