import tkinter as tk
import sto_loot_parser7 as stolp
import os

class STOLootParser:
    def __init__(self, parent):
        self.parent = parent
        self.path_entry = tk.Entry(parent)
        self.path_entry.grid(row=0, column=0)
        self.pasted = tk.IntVar()
        self.pasted_box = tk.Checkbutton(parent, text='Pasted', variable=self.pasted)
        self.pasted_box.grid(row=0, column=1)
        self.populate_button = tk.Button(parent, text='Populate', command=self.populate)
        self.populate_button.grid(row=0, column=2)
        
    def populate(self):
        self.container = stolp.container_from_logs(self.path_entry.get(), self.pasted.get())
        for item in self.container:
            print(item)
            break
            

root = tk.Tk()
parser = STOLootParser(root)
root.mainloop()