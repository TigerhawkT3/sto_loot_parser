import re
import datetime
import sys

year = datetime.datetime.now().year

class Loot:
    def __init__(self, d, t, quantity, item):
        if d:
            month, day = map(int, d.strip('[] ').split('/'))
        else:
            month, day = 1,1
        if t:
            hour, minute = map(int, t.strip('[] ').split(':'))
        else:
            hour, minute = 0, 0
        self.datetime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        
        self.quantity = (int(quantity.strip().replace(',','') or 0) or
                         int(''.join(item.split(' x ')[1:]).replace(',','') or 1))
        self.item = item.split(' x ')[0]
    
    def __str__(self):
        return 'Acquired {} of {} at {}.'.format(self.quantity, self.item, self.datetime)
        
s = '''[3/19] [12:41] [System] [ItemReceived] Items acquired: Astrometric Probes x 10
[12:41] [System] [NumericReceived] You received 1,470 Energy Credits
[12:41] [System] [ItemReceived] Item acquired: Shield Array Mk XII [Pla]'''
#with open(sys.argv[1]) as f:
    # s = f.read()
    
expression = (r'(\[\d+/\d+\] )?(\[\d+:\d+\] )?(?:\[[^]]+\] )?' +
              r'\[(?:NumericReceived|ItemReceived)\] ' +
              r'(?:You received|Items? acquired:) ([0-9,]+ )?(.*)')

loot = [Loot(*result) for result in re.findall(expression, s)]

for match in loot:
    print(match)
