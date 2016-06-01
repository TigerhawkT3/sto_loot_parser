import tkinter as tk
from tkinter import filedialog
import sto_loot_parser as stolp
import os
import datetime
import collections
import sys
import pickle
try:
    import tzlocal
except ImportError:
    tzlocal_present = False
else:
    tzlocal_present = True

class STOLootParser:
    def __init__(self, parent):
        self.parent = parent
        if sys.argv[1:2]:
            self.location = sys.argv[1]
        current_row = 0
        
        self.menubar = tk.Menu(parent)
        
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label='Choose first log file...', command=self.ask_location)
        self.filemenu.add_command(label='Populate', command=self.populate)
        self.filemenu.add_command(label='Save...', command=self.save)
        self.filemenu.add_command(label='Load...', command=self.load)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        
        self.exportmenu = tk.Menu(self.menubar, tearoff=0)
        self.exportmenu.add_command(label='Average per day', command=self.average_per_day)
        self.exportmenu.add_command(label='Totals by day', command=self.totals_by_day)
        self.exportmenu.add_command(label='Cumulative totals by day', command=self.cumulative_totals)
        self.exportmenu.add_command(label='Lockbox winners', command=self.get_winners)
        self.exportmenu.add_command(label='Dabo losses/wins', command=self.dabo)
        self.menubar.add_cascade(label='Export', menu=self.exportmenu)
        
        parent.config(menu=self.menubar)

        self.left_label = tk.Label(parent, text='Key')
        self.left_label.grid(row=current_row, column=0)
        self.right_label = tk.Label(parent, text='Value')
        self.right_label.grid(row=current_row, column=1)
        current_row += 1

        self.filters = [(tk.Entry(parent), tk.Entry(parent)) for i in range(12)]
        for lbl,val in self.filters:
            lbl.grid(row=current_row, column=0)
            val.grid(row=current_row, column=1)
            current_row += 1
        
        self.container = stolp.Container()
    
    def ask_location(self):
        self.location = filedialog.askopenfilename()
        
    def populate(self):
        self.container.extend(stolp.container_from_logs(self.location))
    
    def save(self):
        with open(filedialog.asksaveasfilename(), 'wb') as output:
            pickle.dump(self.container, output)
        
    def load(self):
        with open(filedialog.askopenfilename(), 'rb') as f:
            self.container.extend(pickle.load(f))
        
    def get_filters(self):
        temp = {k.get():v.get() for k,v in self.filters}
        for var in ('min_date', 'max_date'):
            if var in temp:
                temp[var] = datetime.datetime(*map(int, temp[var].split()))
                if tzlocal_present:
                    temp[var] = tzlocal.get_localzone().localize(temp[var])
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
        print('\nLockbox ship winners:')
        print('Date', 'Winner', 'Item', sep='\t')
        for item in self.container.get_winners(**self.get_filters()):
            self.unicode_printer(item.datetime, item.gain_item, item.winner, sep='\t')
            
    def unicode_printer(self, *args, sep=' ', end='\n'):
        *most, last = args
        for arg in most:
            try:
                print(arg, end=sep)
            except UnicodeEncodeError:
                for c in arg:
                    try:
                        print(c, end='')
                    except UnicodeEncodeError:
                        print('?', end='')
                print(end=sep, flush=True)
        try:
            print(last, end=end)
        except UnicodeEncodeError:
            for c in last:
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
        print('\nTotals per day:')
        self.unicode_printer('Date', *headers, sep='\t')
        for d,c in results:
            self.unicode_printer(d, *map(c.get, headers), sep='\t')
    
    def cumulative_totals(self):
        headers = set()
        results = []
        for d,c in self.container.cumulative_totals(**self.get_filters()):
            results.append((datetime.datetime.strftime(d, '%Y-%m-%d'), dict(c)))
            headers |= set(c)
        headers = sorted(headers)
        print('\nCumulative totals per day:')
        self.unicode_printer('Date', *headers, sep='\t')
        for d,c in results:
            self.unicode_printer(d, *map(c.get, headers), sep='\t')
        
    def dabo(self):
        print('\nDabo gambling results:')
        print('Bet', 'Won', sep='\t')
        for l,g in self.container.dabo(**self.get_filters()):
            print(l.loss_value, g.gain_value, sep='\t')
    
    def average_per_day(self):
        print('\nDaily averages:')
        print('Item', 'Average value per day', sep='\t')
        for item in self.container.average_totals(**self.get_filters()).items():
            self.unicode_printer(*item, sep='\t')
            

root = tk.Tk()
parser = STOLootParser(root)
root.mainloop()