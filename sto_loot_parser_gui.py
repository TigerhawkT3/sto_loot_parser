import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import sto_loot_parser as stolp
import os
import datetime
import collections
import sys

class STOLootParser:
    def __init__(self, parent):
        self.parent = parent
        if sys.argv[1:2]:
            self.log_directory = sys.argv[1]
        current_row = 0
        self.pasted = tk.IntVar()
        self.pasted_box = tk.Checkbutton(parent, text='Pasted', variable=self.pasted)
        self.pasted_box.grid(row=current_row, column=0, columnspan=2)
        current_row += 1
        
        self.menubar = tk.Menu(parent)
        
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label='Choose log directory...', command=self.get_log_directory)
        self.filemenu.add_command(label='Populate', command=self.populate)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        
        self.exportmenu = tk.Menu(self.menubar, tearoff=0)
        self.exportmenu.add_command(label='Average per day...', command=self.average_per_day)
        self.exportmenu.add_command(label='Totals by day...', command=self.totals_by_day)
        self.exportmenu.add_command(label='Cumulative totals by day...', command=self.cumulative_totals)
        self.exportmenu.add_command(label='Lockbox winners', command=self.get_winners)
        self.exportmenu.add_command(label='Dabo losses/wins...', command=self.dabo)
        self.menubar.add_cascade(label='Export', menu=self.exportmenu)
        
        parent.config(menu=self.menubar)

        self.filters = [(tk.Entry(parent), tk.Entry(parent)) for i in range(12)]
        for lbl,val in self.filters:
            lbl.grid(row=current_row, column=0)
            val.grid(row=current_row, column=1)
            current_row += 1
    
    def get_log_directory(self):
        self.log_directory = filedialog.askdirectory()
        
    def populate(self):
        self.container = stolp.container_from_logs(self.log_directory, self.pasted.get())
        messagebox.showinfo(title='Done', message='Logs populated.')
    
    def get_filters(self):
        temp = {k.get():v.get() for k,v in self.filters}
        for var in ('min_date', 'max_date'):
            if var in temp:
                temp[var] = datetime.datetime(*map(int, temp[var].split()))
        if 'regex' not in temp:
            for var in ('gain_item', 'loss_item', 'item', 'winner', 'interaction'):
                if var in temp and '|' in temp[var]:
                    temp[var] = {item for item in temp[var].split('|') if item}
        for var in ('min_gain', 'max_gain', 'min_loss', 'max_loss'):
            if var in temp:
                temp[var] = int(temp[var])
        if '' in temp:
            temp.pop('')
            
        return temp
    
    def get_winners(self):
        for item in self.container.get_winners(**self.get_filters()):
            print(item.datetime, end='\t')
            self.unicode_printer(item.gain_item, '\t')
            self.unicode_printer(item.winner, '\n')
            
    def unicode_printer(self, s, end):
        try:
            print(s, end=end)
        except UnicodeEncodeError:
            for c in s:
                try:
                    print(c, end='')
                except UnicodeEncodeError:
                    print('?', end='')
            print(end=end, flush=True)
        
    def totals_by_day(self):
        headers = set()
        results = []
        for d,g,l in self.container.totals_by_day(**self.get_filters()):
            result = collections.Counter(g)
            result.update(l)
            results.append((datetime.datetime.strftime(d, '%Y-%m-%d'), result))
            headers |= set(result)
        headers = sorted(headers)
        print('Date', *headers, sep='\t')
        for d,c in results:
            print(d, *map(c.get, headers), sep='\t')
    
    def cumulative_totals(self):
        headers = set()
        results = []
        for d,c in self.container.cumulative_totals(**self.get_filters()):
            results.append((datetime.datetime.strftime(d, '%Y-%m-%d'), dict(c)))
            headers |= set(c)
        headers = sorted(headers)
        print('Date', *headers, sep='\t')
        for d,c in results:
            print(d, *map(c.get, headers), sep='\t')
        
    def dabo(self):
        for l,g in self.container.dabo(**self.get_filters()):
            print(l.loss_value, g.gain_value, sep='\t')
    
    def average_per_day(self):
        for item in self.container.average_totals(**self.get_filters()).items():
            print(*item, sep='\t')
            

root = tk.Tk()
parser = STOLootParser(root)
root.mainloop()