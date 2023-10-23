#altdialog.py

#Import statements
from customtkinter import *
from tkinter import ttk
import os
import sys
import multiprocessing
from PIL import ImageTk
tempDir = os.path.abspath(__file__)
altdialogpath = os.path.join(tempDir)
rootFolder = os.path.split(altdialogpath)[0]

#We are going to build a similar build of file explorer but in a form of a treeview

class FileSelectWindow(CTkToplevel):
	def populateView(self,treeview, parent, directory):
		items = os.listdir(directory)
		files = []
		for item in items:
			itemPath = os.path.join(directory, item)
			if os.path.isdir(itemPath):
				pass
			else:
				if item.endswith(".jar"):
					files.append(item)
		files.sort()

		for item in files:
			itemPath = os.path.join(directory, item)
			if os.path.isdir(itemPath):
				pass
			else:
				file = treeview.insert(parent, END, text=item, values=("File"))


	def onSelectedFile(self):
		selectedItem = self.fileselection.focus()
		if selectedItem:
			itemText = self.fileselection.item(selectedItem)["text"]
			itemValues = self.fileselection.item(selectedItem)["values"]
			if itemValues[0] == "File":
				selectedPath = self.get_selected_path(self.currentpath, selectedItem)
				self.selected_file = selectedPath
				self.selectedFileAddressBar.delete(0, END)
				self.selectedFileAddressBar.insert(0, selectedPath)
				self.currentfileString = str(selectedPath)
				os.chdir(self.currentpath)
				self.root.destroy()

	def get_selected_path(self, directory, item):
		itemText = self.fileselection.item(item)["text"]
		itemParent = self.fileselection.parent(item)
		if itemParent:
			parentPath = self.get_selected_path(directory, itemParent)
			selectedPath = os.path.join(parentPath, itemText)
		else:
			selectedPath = os.path.join(directory, itemText)
		return selectedPath

	def updateView(self, directory):
		self.fileselection.delete(*self.fileselection.get_children())
		self.currentpath = directory  # Update the current directory
		self.populateView(self.fileselection, "", directory)
	
	def passrootDirectory(self,directory):
		self.rootDir = directory
		return
	
	def getRoot(self):
		return self.rootDir

	def getSelectedFile(self):
		return self.selected_file
	
	def getFilepathString(self):
		return self.currentfileString

	def getClosedWindowBool(self):
		return self.closedWindow
	
	def getcurrentpath(self):
		return self.currentpath

	def onWindowClose(self):
		self.closedWindow = True
		self.root.destroy()

	def __init__(self, parent, **kwargs):
		self.queue = multiprocessing.Queue()
		self.parent = parent
		self.selected_file = None
		self.currentfileString = ''
		self.rootDir = ''
		self.currentpath = str(rootFolder)  # Set the initial current directory
		self.closedWindow = False
		#Doesnt work, will fix later
		#self.iconpath = ImageTk.PhotoImage(file=os.path.join(str(self.rootDir),"base/ui/default.png"))
		#self.wm_iconbitmap()
		#self.after(300, lambda: self.iconphoto(False, self.iconpath))
		self.root = CTkToplevel()
		self.root.title("Select File")
		self.root.geometry('800x270')
		self.root.resizable(False, False)
		self.root.protocol("WM_DELETE_WINDOW", self.onWindowClose)
		self.treeviewCanvas = CTkCanvas(self.root,highlightthickness=0)
		self.treeviewCanvas.pack(fill=BOTH,padx=5)
		self.treeviewScrollbar = CTkScrollbar(self.treeviewCanvas)
		self.treeviewScrollbar.pack(fill=BOTH,side=RIGHT)
		self.fileselection = ttk.Treeview(self.treeviewCanvas,yscrollcommand=self.treeviewScrollbar.set)
		self.fileselection.pack(fill="both", side="top")
		self.treeviewScrollbar.configure(command=self.fileselection.yview)
		self.fileselection["columns"] = ("Type",)
		self.fileselection.column("#0", width=200)
		self.fileselection.column("Type", width=100)
		self.fileselection.heading("#0", text="Name")
		self.fileselection.heading("Type", text="Type")
		self.populateView(self.fileselection, "", self.currentpath)  # Populate the initial view

		self.selectedFileLabel = CTkLabel(self.root, text="Filepath: ")
		self.selectedFileLabel.pack(after=self.treeviewCanvas,side=LEFT,anchor=E)
		self.selectedFileAddressBar = CTkEntry(self.root)
		self.selectedFileAddressBar.pack(after=self.selectedFileLabel,fill=X,expand=True,side=LEFT,anchor=W)
		self.selectbtn = CTkButton(self.root, text="Select File", command=self.onSelectedFile)
		self.selectbtn.pack(after=self.selectedFileAddressBar,side=LEFT,anchor=E,padx=5)

		def update_selected_file(event):
			selected_item = self.fileselection.focus()
			if selected_item:
				item_text = self.fileselection.item(selected_item)["text"]
				item_values = self.fileselection.item(selected_item)["values"]
				if item_values[0] == "Folder":
					selectedPath = self.get_selected_path(self.currentpath, selected_item)
					self.currentpath = selectedPath  # Update the current directory
					self.updateView(selectedPath)
				if item_values[0] == "File":
					current_directory = self.currentpath  # Use the current directory
					self.selected_file = os.path.join(current_directory, item_text)
					self.selectedFileAddressBar.delete(0, END)
					self.selectedFileAddressBar.insert(END, self.selected_file)

		self.fileselection.bind("<<TreeviewSelect>>", update_selected_file)

	def haltbackgroundexecution(self):
		self.root.wait_window(self.root)