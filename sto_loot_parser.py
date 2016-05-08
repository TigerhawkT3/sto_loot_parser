import re
import datetime
import sys

year = datetime.datetime.now().year

class Loot:
    def __init__(self, d, t, category, interaction, acquired, winner, quantity, item):
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
        
        item = item.split(' x ')[0]
        
        if interaction == 'lost':
            self.gain = None
            self.loss = (item, quantity * -1)
        elif interaction == 'sold':
            item, gain = item.rsplit(' for ', maxsplit=1)
            self.loss = (item, -1)
            quantity, item = gain.split(maxsplit=1)
            self.gain = (item, int(quantity.replace(',', '')))
        elif interaction == 'received' or acquired:
            self.gain = (item, quantity)
            self.loss = None
        else:
            self.gain = (item, quantity)
            self.loss = None
    
    def __str__(self):
        if self.winner:
            return '{} won {}.'.format(self.winner, self.gain[0])
        
        if self.gain:
            gain = 'Gained {} x{}.'.format(*self.gain)
        else:
            gain = 'No gains.'
        if self.loss:
            loss = 'Lost {} x{}.'.format(self.loss[0], self.loss[1]*-1)
        else:
            loss = 'No losses.'
        
        return '{}: {} {}'.format(self.datetime, gain, loss)
        
s = '''[3/19 12:41] [System] [ItemReceived] Items acquired: Astrometric Probes x 10
[3/19 12:41] [System] [ItemReceived] Items acquired: Astrometric Probes x 10
[12:41] [System] [NumericReceived] You received 1,470 Energy Credits
[12:41] [System] [ItemReceived] Item acquired: Shield Array Mk XII [Pla]
[5/5] [System] [ItemReceived] Item acquired: Z-Particle
[5/5 6:22] [System] Item acquired: Beta-Tachyon Particle
[5/7 2:18] [System] [NumericReceived] You sold Console - Engineering - EPS Flow Regulator for 2,763 Energy Credits
[5/7 2:18] [System] [NumericReceived] You sold Industrial Replicators for 100,000 Energy Credits
[12:40] [System] [NumericLost] You lost 1 Pass Token
[5/6 12:31] [System] [GameplayAnnounce] Sven@maxbuy2 hat einen Na'kuhl-Tadaari-Raider [K6] erhalten!
[5/6 12:32] [System] [GameplayAnnounce] R. Brent@baldor6 hat einen Herold-Vonph-Dreadnought-Träger [K6] erhalten!
[5/6 12:33] [System] [GameplayAnnounce] Gareth@l0rdgareth has acquired a Tholian Tarantula Dreadnought Cruiser [T6]!
[5/6 12:46] [System] [GameplayAnnounce] Seven@lynnnick01 has acquired a Na'kuhl Tadaari Raider [T6]!'''
#with open(sys.argv[1]) as f:
    #pass
    
expression = (r'^(?:\[(\d+/\d+)? ?(\d+:\d+)?\] )?(?:\[[^]]+\] )?' +
              r'(?:\[(NumericReceived|ItemReceived|NumericLost|GameplayAnnounce)\] )?' +
              r'(?:You (lost|received|sold)|Items? (acquired):|(.*) (?:has acquired|hat einen))' +
              r' ([0-9,]+ )?(.*)')

loot = [Loot(*match.groups()) for match in (re.match(expression, line) for line in s.split('\n')) if match]

for match in loot:
    print(match)
    
    
    
    
    
    
    