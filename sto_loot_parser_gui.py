import tkinter as tk
import sto_loot_parser as stolp
import os
import datetime
import collections

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
        self.dabo_button = tk.Button(parent, text='Dabo wins/losses', command=self.dabo)
        self.dabo_button.grid(row=current_row, column=1)
        self.average_button = tk.Button(parent, text='Avg per day', command=self.average_per_day)
        self.average_button.grid(row=current_row, column=2)
        self.winners_button = tk.Button(parent, text='Lockbox wins', command=self.get_winners)
        self.winners_button.grid(row=current_row, column=3)
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
            print(datetime.datetime.strftime(item.datetime, '%y-%m-%d %H:%M:%S'), end='\t')
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
                print(end, end='', flush=True)
        
    def totals_by_day(self, category='net'):
        headers = set()
        results = []
        for d,g,l in self.container.totals_by_day(**self.get_filters()):
            result = collections.Counter(g)
            result.update(l)
            results.append((datetime.datetime.strftime(d, '%y-%m-%d'),result))
            headers |= set(result)
        headers = sorted(headers)
        print('Date', *headers, sep='\t')
        for d,c in results:
            print(d, *map(c.get, headers), sep='\t')
    
    def dabo(self):
        for item in self.container.dabo(**self.get_filters()):
            print(*item)
    
    def average_per_day(self):
        for item in self.container.average_totals(**self.get_filters()).items():
            print(*item, sep='\t')
            

root = tk.Tk()
parser = STOLootParser(root)
root.mainloop()