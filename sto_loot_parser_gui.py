import tkinter as tk
import sto_loot_parser as stolp
import os
import datetime

class STOLootParser:
    def __init__(self, parent):
        self.parent = parent
        self.path_entry = tk.Entry(parent)
        current_row = 0
        self.path_entry.grid(row=current_row, column=0)
        self.pasted = tk.IntVar()
        self.pasted_box = tk.Checkbutton(parent, text='Pasted', variable=self.pasted)
        self.pasted_box.grid(row=current_row, column=1)
        self.populate_button = tk.Button(parent, text='Populate', command=self.populate)
        self.populate_button.grid(row=current_row, column=2)
        current_row += 1
        self.totals_by_day_button = tk.Button(parent, text='Totals by day', command=self.totals_by_day)
        self.totals_by_day_button.grid(row=current_row, column=0)
        current_row += 1
        self.filters = [(tk.Entry(parent), tk.Entry(parent)) for i in range(12)]
        for lbl,val in self.filters:
            lbl.grid(row=current_row, column=0)
            val.grid(row=current_row, column=1)
            current_row += 1
        
    def populate(self):
        self.container = stolp.container_from_logs(self.path_entry.get(), self.pasted.get())
    
    def get_filters(self):
        temp = {k.get():v.get() for k,v in self.filters}
        if 'min_date' in temp:
            temp['min_date'] = datetime.datetime(*map(int, temp['min_date'].split()))
        if 'max_date' in temp:
            temp['max_date'] = datetime.datetime(*map(int, temp['max_date'].split()))
        if '' in temp:
            temp.pop('')
        return temp
    
    def totals_by_day(self):
        for d,i in self.container.totals_by_day(**self.get_filters()):
            print(datetime.datetime.strftime(d, '%y-%m-%d'), i)
            

root = tk.Tk()
parser = STOLootParser(root)
root.mainloop()