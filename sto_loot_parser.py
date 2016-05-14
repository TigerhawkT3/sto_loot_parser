import re
import datetime
import sys
import collections

now = datetime.datetime.now()
year = now.year
min_date = datetime.datetime(1, 1, 1)

class Container:
    def __init__(self):
        self.bag = []
    
    def add(self, loot):
        self.bag.append(loot)
    
    def __add__(self, other):
        temp = Container()
        temp.bag = self.bag + other.bag
        return temp
    
    def extend(self, other):
        self.bag.extend(other.bag)
    
    def __bool__(self):
        return bool(self.bag)
        
    def __iter__(self):
        return iter(self.bag)
    
    def get_loot(self, **filters):
        ranges = {k:filters.pop(k) if k in filters else v
                for k,v in (('min_date', min_date), ('max_date', now),
                            ('min_gain', 0), ('max_gain', 10000000000),
                            ('min_loss', 0), ('max_loss', -10000000000))}
        for event in self:
            if (ranges['min_date'] <= event.datetime <= ranges['max_date']
            ) and (ranges['min_gain'] <= event.gain_value <= ranges['max_gain']
            ) and (ranges['max_loss'] <= event.loss_value <= ranges['min_loss']) and all(
                v in getattr(event, k) for k,v in filters.items()):
                yield event
                
    def average_value_per_event(self, loss=False, **filters):
        total = 0
        length = 0
        for item in self.get_loot(**filters):
            if loss:
                total += item.loss_value
            else:
                total += item.gain_value
            length += 1
        return total/length
    
    def event_quantity(self, loss=False, **filters):
        return sum(1 for item in self.get_loot(**filters) if (
                    item.loss_item and loss) or (item.gain_item and not loss))
    
    def total_value(self, loss=False, **filters):
        return sum(item.loss_value if loss else item.gain_value for item in
                    self.get_loot(**filters))
    
    def group_by_day(self, calendar=False, **filters):
        bucket = []
        loot = iter(self.get_loot(**filters))
        item = next(loot)
        bucket.append(item)
        start_date = item.datetime
        m,d = item.datetime.month, item.datetime.day
        for item in loot:
            if (m == item.datetime.month and d == item.datetime.day) if calendar else (
                    item.datetime < start_date + datetime.timedelta(1)):
                bucket.append(item)
            else:
                yield bucket
                bucket = []
                start_date = item.datetime
                m,d = item.datetime.month, item.datetime.day
                bucket.append(item)
        if bucket:
            yield bucket
    
    def totals_by_day(self, **filters):
        for bucket in self.group_by_day(**filters):
            items = {}
            for item in bucket:
                items[item.gain_item] = items.get(item.gain_item, 0) + item.gain_value
                items[item.loss_item] = items.get(item.loss_item, 0) + item.loss_value
            if '' in items:
                items.pop('')
            yield items
    
    def counter(self, **filters):
        return collections.Counter(val for item in self.get_loot(**filters)
                                    for val in (item.loss_item, item.gain_item) if val)
        
    def common(self, least=False, counter=None, **filters):
        if counter:
            return counter.most_common()[-1*least]
        return self.counter(**filters).most_common()[-1*least]
    
    def __str__(self):
        return '\n'.join(str(item) for item in self)
    
    def __repr__(self):
        return str(self)

class Loot:
    def __init__(self, d, t, interaction, winner, quantity, item):
        if d:
            month, day = map(int, d.strip('[] ').split('/'))
        else:
            month, day = 1,1
        if t:
            hour, minute = map(int, t.strip('[] ').split(':'))
        else:
            hour, minute = 0, 0
        self.datetime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        
        self.winner = winner
        
        quantity = quantity or ''
        quantity = (int(quantity.strip().replace(',','') or 0) or
                         int(''.join(item.split(' x ')[1:]).replace(',','') or 1))
        
        item = item.split(' x ')[0].rstrip('!.').rsplit(' erhalten', maxsplit=1)[0]
        
        self.interaction = interaction
        
        if interaction in {'lost', 'placed a bet of', 'discarded', 'spent'}:
            self.gain_item = ''
            self.gain_value = 0
            self.loss_item = item
            self.loss_value = quantity * -1
        elif interaction == 'sold':
            item, gain = item.rsplit(' for ', maxsplit=1)
            self.loss_item = item
            self.loss_value = -1
            quantity, item = gain.split(maxsplit=1)
            self.gain_item = item
            self.gain_value = int(quantity.replace(',', ''))
        elif interaction == "didn't win any":
            self.gain_item = item
            self.gain_value = 0
            self.loss_item = ''
            self.loss_value = 0
        else:
            self.gain_item = item
            self.gain_value = quantity
            self.loss_item = ''
            self.loss_value = 0
    
    def __str__(self):
        if self.winner:
            return '{} won {}.'.format(self.winner, self.gain_item)
        
        if self.gain_item:
            gain = 'Gained {} x{}.'.format(self.gain_item, self.gain_value)
        else:
            gain = 'No gains.'
        if self.loss_item:
            loss = 'Lost {} x{}.'.format(self.loss_item, self.loss_value*-1)
        else:
            loss = 'No losses.'
        
        return '{}: {} {}'.format(self.datetime, gain, loss)
    
    def __repr__(self):
        return str(self)

s = '''[3/19 12:41] [System] [ItemReceived] Items acquired: Astrometric Probes x 10
[3/19 12:41] [System] [ItemReceived] Items acquired: Astrometric Probes x 10
[12:41] [System] [NumericReceived] You received 1,470 Energy Credits
[12:41] [System] [ItemReceived] Item acquired: Shield Array Mk XII [Pla]
[5/5] [System] [ItemReceived] Item acquired: Z-Particle
[5/5 6:22] [System] Item acquired: Beta-Tachyon Particle
[12:40] [System] [NumericLost] You lost 1 Pass Token
[5/6 12:31] [System] [GameplayAnnounce] Sven@maxbuy2 hat einen Na'kuhl-Tadaari-Raider [K6] erhalten!
[5/6 12:32] [System] [GameplayAnnounce] R. Brent@baldor6 hat einen Herold-Vonph-Dreadnought-Träger [K6] erhalten!
[5/6 12:33] [System] [GameplayAnnounce] Gareth@l0rdgareth has acquired a Tholian Tarantula Dreadnought Cruiser [T6]!
[5/6 12:46] [System] [GameplayAnnounce] Seven@lynnnick01 has acquired a Na'kuhl Tadaari Raider [T6]!
[5/7 2:18] [System] [NumericReceived] You sold Console - Engineering - EPS Flow Regulator for 2,763 Energy Credits
[5/7 2:18] [System] [NumericReceived] You sold Industrial Replicators for 100,000 Energy Credits
[5/8 3:10] [Minigame] Gloria placed a bet of 100 Energy Credits.
[5/8 3:10] [System] [Default] You placed a bet of 100 Energy Credits.
[5/8 3:10] [Minigame] Gloria placed a bet of 100 Energy Credits.
[5/8 3:10] [System] [Default] You placed a bet of 100 Energy Credits.
[5/8 3:10] [Minigame] Gloria placed a bet of 100 Energy Credits.
[5/8 3:10] [System] [Default] You placed a bet of 100 Energy Credits.
[5/8 3:10] [Minigame] Rudy placed a bet of 100 Energy Credits.
[5/8 3:10] [Minigame] Rudy placed a bet of 100 Energy Credits.
[5/8 3:10] [Minigame] Rudy placed a bet of 100 Energy Credits.
[5/8 3:11] [System] [Default] You won 150 Gold-Pressed Latinum.
[5/8 3:11] [System] [Default] You won 150 Gold-Pressed Latinum.
[5/8 3:11] [System] [Default] You won 10 Gold-Pressed Latinum.
[5/12 2:32] [Minigame] Gloria placed a bet of 100 Energy Credits.
[5/12 2:32] [System] [Default] You placed a bet of 100 Energy Credits.
[5/12 2:32] [System] [Default] You didn't win any Gold-Pressed Latinum.'''
#with open(sys.argv[1]) as f:
    #pass
    
expression = (r'^(?:\[(\d+/\d+)? ?(\d+:\d+)?\] )?(?:\[[^]]+\] )?' +
              r'(?:\[(?:NumericReceived|ItemReceived|NumericLost|GameplayAnnounce|Default)\] )?' +
              r"(?:You (didn't win any|spent|discarded|lost|refined"
              r"|received|sold|placed a bet of|won)|Items? acquired:|(.*) "
              r'(?:has acquired an?|hat einen))' +
              r' ([0-9,]+ )?(.*)')

container = Container()
for loot in (Loot(*match.groups()) for match in (re.match(expression, line) for line in s.split('\n')) if match):
    container.add(loot)

for match in container.get_loot(gain_item='Energy Credits', min_date=datetime.datetime(2016,4,1)):
    print(match)

print(container.average_value_per_event(loss=True, gain_item='Energy Credits', min_date=datetime.datetime(2016,4,1)))

count = container.counter()

print(count)

print(container.common(counter=count, least=True))

print(container.event_quantity(gain_item='Energy Credits'))

print(container.total_value(gain_item='Energy Credits'))

for bucket in container.group_by_day(min_date=datetime.datetime(2016, 5, 6)):
    print(bucket)

for day in container.totals_by_day(min_date=datetime.datetime(2016, 5, 6)):
    print(day)

for bucket in container.group_by_day(calendar=True, min_date=datetime.datetime(2016, 5, 6)):
    print(bucket)

for day in container.totals_by_day(calendar=True, min_date=datetime.datetime(2016, 5, 6)):
    print(day)
    
    
    
    
    
    
    
    
    
    

