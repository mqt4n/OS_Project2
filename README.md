# 📁 File Explorer for NTFS and FAT32 Partitions 🔍

## 🗂️ Overview
This project is a Python-based file explorer that can read and display files and directories from NTFS and FAT32 partitions on removable media (USB drives). It provides a graphical user interface to navigate the file system, view file properties, and read text file contents.

## ✨ Features
- 💽 Supports both NTFS and FAT32 file systems
- 🌳 Displays file hierarchy in a tree view
- 📝 Shows detailed file information (name, attributes, size, dates)
- 👁️ Allows viewing text file contents
- 🔄 Refresh functionality to reload disk data
- 🖼️ Icons for different file types

## 📋 Requirements
- 🐍 Python 3.x
- 📦 Required Python packages:
  - `wmi` (for Windows Management Instrumentation)
  - `tkinter` (for GUI)
  - `Pillow` (for image handling)

## ⚙️ Installation
1. Clone or download the repository
2. Install the required packages:
   ```
   pip install wmi Pillow
   ```

## 🚀 Usage
1. 💾 Connect a USB drive with NTFS or FAT32 partitions to your computer
2. Run the application by administrator privileges:
   ```
   python main.py
   ```
3. The application will:
- 🔍 Detect removable media
- 📊 Read partition tables
- 🔠 Parse NTFS and FAT32 file systems
- 🖥️ Display the file hierarchy in a graphical interface

## 📂 File Structure
- `main.py`: Main application with GUI
- `NTFS.py`: NTFS file system parser
- `FAT32.py`: FAT32 file system parser
- `asset/`: Directory containing icon images

## 🎛️ Controls
- 📂 Click on folders to expand/collapse directory structure
- 📄 Select files to view their properties and content
- 🔄 Use the refresh button to reload data from disk

## ℹ️ Notes
- The application is designed for Windows systems
- Only text file contents can be displayed (other file types will show size and attributes only)
- The application requires administrator privileges to access raw disk data

## ❓ Troubleshooting
If you encounter errors:
1. 🔌 Ensure the USB drive is properly connected
2. 🔒 Verify you have administrator privileges
3. 💽 Check that the drive has either NTFS or FAT32 partitions
4. 📦 Make sure all required Python packages are installed

## ©️ License
This project is provided as-is without warranty. You are free to use and modify the code for educational purposes.