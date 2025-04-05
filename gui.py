import os 
import tkinter as tk 
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from PIL import Image, ImageTk

class Entry:
	def __init__(self, id, name, is_folder, parentID=None, size=None, created_date=None, modified_date=None, content=None): 
		self.id = id
		self.name = name
		self.is_folder = is_folder
		self.parentId = parentID
		self.size = size 
		self.created_date = created_date or datetime.now()
		self.modified_date = modified_date or datetime.now()
		self.content = content 
		

class App:
	def __init__(self, root, entries):
		self.root = root 
		self.root.title("App") 
		self.root.geometry("900x600")
		self.root.configure(bg="white") 

		self.entries = entries 
		self.entry_dict = {entry.id: entry for entry in entries} 

		self.style = ttk.Style() 
		self.style.configure("TFrame", background="white")
		self.style.configure("TLabel", background="white")
		self.style.configure("Treeview", background="white", fieldbackground="white")
		self.style.map("Treeview", background=[("selected", "#0078d7")])
		self.style.configure("TNotebook", background="white")
		self.style.configure("TNotebook.Tab", background="white", padding=[10, 5])

		# icon 
		self.load_icons() 

		# toolbar 
		self.toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg="white")
		self.toolbar.pack(side=tk.TOP, fill=tk.X) 

		# create paned window 
		self.paned_window = tk.PanedWindow(
			self.root, 
			orient=tk.HORIZONTAL, 
			bg="white",
			sashwidth=5, 
			sashrelief=tk.RAISED,
			sashpad=2, 
			opaqueresize=False
		)

		self.paned_window.pack(fill=tk.BOTH, expand=True) 

		# left frame for directory tree 
		self.tree_frame = tk.Frame(self.paned_window, width=300, bg="white", bd=2, relief=tk.GROOVE)
		self.tree = ttk.Treeview(self.tree_frame) 
		self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) 

		# right frame for detail 
		self.detail_frame = tk.Frame(self.paned_window, bg="white", bd=2, relief=tk.GROOVE)

		self.notebook = ttk.Notebook(self.detail_frame)
		self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) 
		
		self.info_tab = tk.Frame(self.notebook, bg="white")
		self.notebook.add(self.info_tab, text="Thông tin") 

		self.labels = {
			'name': tk.Label(self.info_tab, text="Tên: ",anchor='w', bg="white"),
			'size': tk.Label(self.info_tab, text="Kích thước: ",anchor='w', bg="white"),
			'created': tk.Label(self.info_tab, text="Ngày tạo: ",anchor='w', bg="white"),
			'modified': tk.Label(self.info_tab, text="Ngày sửa: ",anchor='w', bg="white"),
			'attributes': tk.Label(self.info_tab, text="Thuộc tính:", anchor='w', bg="white")
		}

		for i, label in enumerate(self.labels.values()):
			label.grid(row=i, column=0, sticky='ew', padx=5, pady=2) 

		self.tree.bind("<<TreeviewOpen>>", self.click_folder)
		self.tree.bind("<<TreeviewSelect>>", self.show_entry_info)
			
			# show content (only text file) 
		self.content_tab = tk.Frame(self.notebook, bg="white")
		self.notebook.add(self.content_tab, text="Nội dung")

		self.content_text = scrolledtext.ScrolledText(
			self.content_tab, 
			wrap=tk.WORD, 
			state='disabled',
			bg="white", 
			bd=1, 
			relief=tk.SOLID,
			highlightbackground="#a9d1f7",
			highlightthickness=1
		)
		
		self.content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) 

		# add frame into panded window 
		self.paned_window.add(self.tree_frame)
		self.paned_window.add(self.detail_frame) 

		self.initial()

	def initial(self):
		for entry in self.entries:
			if entry.parentId == None: self.add_entry('', entry) 
	
	def add_entry(self, parent, entry):
		if entry.is_folder:
			item = self.tree.insert(
				parent, 'end', entry.id, 
				text=entry.name,
				values=('folder',), 
				image=self.folder_icon
			)

			# if any(e.parentId == entry.id for e in self.entries):
			# 	self.tree.insert(item, 'end', ) 
			self.tree.insert(item, 'end')
			
			self.tree.item(item, open=False)
		else:
			self.tree.insert(
				parent, 'end', entry.id, 
				text=entry.name, 
				values=('folder'), 
				image=self.file_icon
			)

	def click_folder(self, event):
		item = self.tree.focus() 
		if not item:
			return 
		
		entry = self.entry_dict.get(item) 
		if not entry or not entry.is_folder:
			return 
		
		childrent = self.tree.get_children(item)
		if childrent:
			for child in childrent:
				self.tree.delete(child) 
		else:
			for subentry in self.entries:
				if subentry.parentId == entry.id:
					self.add_entry(item, subentry)


	def show_entry_info(self, event=None):
		item = self.tree.focus()
		if not item: return
        
		entry = self.entry_dict.get(item)
		if not entry: return
        
		created = entry.created_date.strftime('%Y-%m-%d %H:%M:%S') if entry.created_date else "Không rõ" 
		modified = entry.modified_date.strftime('%Y-%m-%d %H:%M:%S') if entry.modified_date else "Không rõ"
        
		self.labels['name'].config(text=f"Tên: {entry.name}")
		self.labels['size'].config(text=f"Kích thước: {self.format_size(entry.size) if entry.size else 'N/A'}")
		self.labels['created'].config(text=f"Ngày tạo: {created}")
		self.labels['modified'].config(text=f"Ngày sửa: {modified}")
		self.labels['attributes'].config(text=f"Loại: {'Thư mục' if entry.is_folder else 'File'}")
        
		self.notebook.select(self.info_tab)
	
	def load_icons(self):
		try:
			folder_img = Image.open("asset/folder.png").resize((16, 16))
			file_img = Image.open("asset/file.png").resize((16, 16))

			self.folder_icon = ImageTk.PhotoImage(folder_img) 
			self.file_icon = ImageTk.PhotoImage(file_img) 
		except:
			self.folder_icon = self.file_icon = "" 

	def format_size(self, size):
		if size is None:
			return "N/A"
		for unit in ['B', 'KB', 'MB', 'GB']:
			if size < 1024.0:
				return f"{size:.2f} {unit}"
			size /= 1024.0
		
		return f"{size:.2f} TB"

if __name__ == "__main__":

	entries = [
		Entry("root1", "Folder 1", True),
        Entry("file1", "File 1.txt", False, "root1", 1024, content="Nội dung file 1"),
        Entry("root2", "Folder 2", True),
        Entry("folder1", "Thư mục con", True, "root2"),
        Entry("file2", "File 2.txt", False, "folder1", 2048, content="Nội dung file 2"),
        Entry("file3", "File 3.txt", False, "root2", 512, content="Nội dung file 3"),
	]
	
	root = tk.Tk() 
	app = App(root, entries)
	root.mainloop()  
