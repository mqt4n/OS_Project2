import os
import wmi
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from PIL import Image, ImageTk
from NTFS import *

# Class đại diện cho 1 mục (file hoặc thư mục)
class Entry:
    def __init__(self, selfid, name, is_folder, parentID, size, created_date, modified_date, content):
        self.id = selfid
        self.name = name
        self.is_folder = is_folder
        self.parentId = parentID
        self.size = size
        self.created_date = created_date
        self.modified_date = modified_date
        self.content = content

# Ứng dụng chính
class App:
    def __init__(self, root, entries):
        self.root = root
        self.root.title("App")
        self.root.geometry("900x600")
        self.root.configure(bg="white")

        self.entries = entries
        self.entry_dict = {entry.id: entry for entry in entries}  # Dễ tra cứu theo id
        for entry in self.entry_dict.values():
            print(f"ID: {entry.id}, Name: {entry.name}, Parent ID: {entry.parentId}")
        self.configure_style()
        self.load_icons()
        self.create_toolbar()
        self.create_main_ui()
        self.initial()

    # Cài đặt giao diện
    def configure_style(self):
        self.style = ttk.Style()
        self.style.configure("TFrame", background="white")
        self.style.configure("TLabel", background="white")
        self.style.configure("Treeview", background="white", fieldbackground="white")
        self.style.map("Treeview", background=[("selected", "#0078d7")])
        self.style.configure("TNotebook", background="white")
        self.style.configure("TNotebook.Tab", background="white", padding=[10, 5])

    # Tải biểu tượng thư mục và file
    def load_icons(self):
        try:
            folder_img = Image.open("asset/folder.png").resize((16, 16))
            file_img = Image.open("asset/file.png").resize((16, 16))
            self.folder_icon = ImageTk.PhotoImage(folder_img)
            self.file_icon = ImageTk.PhotoImage(file_img)
        except:
            self.folder_icon = self.file_icon = ""

    # Thanh công cụ trên cùng
    def create_toolbar(self):
        self.toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg="white")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

    # Tạo giao diện chính
    def create_main_ui(self):
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="white",
                                           sashwidth=5, sashrelief=tk.RAISED, sashpad=2, opaqueresize=False)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Khung cây thư mục bên trái
        self.tree_frame = tk.Frame(self.paned_window, width=300, bg="white", bd=2, relief=tk.GROOVE)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewOpen>>", self.click_folder)
        self.tree.bind("<<TreeviewSelect>>", self.show_entry_info)

        # Khung chi tiết bên phải
        self.detail_frame = tk.Frame(self.paned_window, bg="white", bd=2, relief=tk.GROOVE)
        self.notebook = ttk.Notebook(self.detail_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab thông tin
        self.info_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.info_tab, text="Thông tin")
        self.labels = {
            'name': tk.Label(self.info_tab, text="Tên: ", anchor='w', bg="white"),
            'size': tk.Label(self.info_tab, text="Kích thước: ", anchor='w', bg="white"),
            'created': tk.Label(self.info_tab, text="Ngày tạo: ", anchor='w', bg="white"),
            'modified': tk.Label(self.info_tab, text="Ngày sửa: ", anchor='w', bg="white"),
            'attributes': tk.Label(self.info_tab, text="Thuộc tính:", anchor='w', bg="white")
        }
        for i, label in enumerate(self.labels.values()):
            label.grid(row=i, column=0, sticky='ew', padx=5, pady=2)

        # Tab nội dung file
        self.content_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.content_tab, text="Nội dung")
        self.content_text = scrolledtext.ScrolledText(self.content_tab, wrap=tk.WORD, state='disabled',
                                                       bg="white", bd=1, relief=tk.SOLID,
                                                       highlightbackground="#a9d1f7", highlightthickness=1)
        self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Thêm 2 khung vào cửa sổ chia
        self.paned_window.add(self.tree_frame)
        self.paned_window.add(self.detail_frame)

    # Khởi tạo cây thư mục từ danh sách entry
    def initial(self):
        for entry in self.entries:
            if entry.parentId is None:
                self.add_entry('', entry)

    # Thêm entry vào cây thư mục
    def add_entry(self, parent, entry):
        if entry.is_folder:
            item = self.tree.insert(parent, 'end', entry.id, text=entry.name,
                                    values=('folder',), image=self.folder_icon)
            self.tree.insert(item, 'end')  # Thêm dòng ảo để hiển thị nút mở rộng
            self.tree.item(item, open=False)
        else:
            self.tree.insert(parent, 'end', entry.id, text=entry.name,
                             values=('file',), image=self.file_icon)

    # Khi mở thư mục trong cây
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

    # Hiển thị thông tin mục đang chọn
    def show_entry_info(self, event=None):
        item = self.tree.focus()
        if not item:
            return

        entry = self.entry_dict.get(item)
        if not entry:
            return

        created = str(entry.created_date)
        modified = str(entry.modified_date)

        self.labels['name'].config(text=f"Tên: {entry.name}")
        self.labels['size'].config(text=f"Kích thước: {self.format_size(entry.size) if entry.size else 'N/A'}")
        self.labels['created'].config(text=f"Ngày tạo: {created}")
        self.labels['modified'].config(text=f"Ngày sửa: {modified}")
        self.labels['attributes'].config(text=f"Loại: {'Thư mục' if entry.is_folder else 'File'}")

        # Nếu là file, hiển thị nội dung của file vào tab nội dung
        if not entry.is_folder:
            self.show_file_content(entry)

        self.notebook.select(self.info_tab)

# Đọc và hiển thị nội dung của file từ entry.content
    def show_file_content(self, entry):
        self.content_text.config(state='normal')  # Bật chế độ sửa để cập nhật nội dung
        self.content_text.delete(1.0, tk.END)  # Xóa nội dung cũ

        if entry.content:
            # Hiển thị nội dung của file nếu có trong entry.content
            self.content_text.insert(tk.END, entry.content)
        else:
            # Nếu không có nội dung, hiển thị thông báo
            self.content_text.insert(tk.END, "Không có nội dung.")

        self.content_text.config(state='disabled')  # Đặt lại chế độ chỉ đọc sau khi hiển thị


    # Định dạng kích thước file
    def format_size(self, size):
        if size is None:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

# Khởi chạy chương trình
if __name__ == "__main__":
    c = wmi.WMI()
    partition = []

    # Lấy danh sách các ổ đĩa vật lý
    for disk in c.Win32_DiskDrive():
        if disk.MediaType == "Removable Media":
            usb = disk
    fin = open(usb.DeviceID, "rb")
    bootloader = fin.read(446)
    entries = []
    arr = ["FAT32", "NTFS"]
    for i in range(4):
        par = fin.read(16)
        partition.append(Partition(par, usb.DeviceID))
        if partition[i].type == "NTFS":
            main = NTFS(partition[i])
            list_file = main.get_list_file()
            # "ID": self.get_id(),
            # "Name": self.get_file_name(),
            # "Is Folder": self.is_folder(),
            # "Parent ID": self.get_parent_id(),
            # "Size": self.get_size(),
            # "Create Time": self.get_create_time(),
            # "Modify Time": self.get_modify_time(),
            # "Data": self.get_data(),
            print(list_file.__len__())
            for entry in list_file:
                print(f"Name: {entry['Name']}")
            for entry in list_file:
                entries.append(Entry(entry["ID"], entry["Name"], entry["Is Folder"],
                                    entry["Parent ID"], entry["Size"], entry["Create Time"],
                                    entry["Modify Time"], entry["Data"]))
            
        
    fin.close()


    root = tk.Tk()
    app = App(root, entries)
    root.mainloop()
