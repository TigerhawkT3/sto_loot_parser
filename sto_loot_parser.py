import re
import datetime
import time
import sys
import collections
import os
import pickle

try:
    import tzlocal
except ImportError:
    tzlocal_present = False
else:
    tzlocal_present = True

now = datetime.datetime.now()
min_date = datetime.datetime(2002, 1, 1)
year = now.year

if tzlocal_present:
    now = tzlocal.get_localzone().localize(now)
    min_date = tzlocal.get_localzone().localize(min_date)

def container_from_logs(location, cp=False):
    '''
    Parses log files (starting) from the given location and creates
    a Container object to hold the created Loot objects.
    Parameters:
        location (str): the location of a pasted log, or the
            location of the first chatlog in a series
        cp (bool): whether the parser should read a single log file
            with the copy-paste syntax rather than the default behavior
            of reading every available log file starting from the given
            one and using the saved-logfile syntax
    Returns:
        Container: populated with Loot objects
    '''
    paste = (r'^(?:\[(\d+/\d+)? ?(\d+:\d+)?\] )?(?:\[[^]]+\] )?'
          r'(?:\[(?:NumericReceived|ItemReceived|NumericLost|GameplayAnnounce|Default)\] )?'
          )

    log = r'^\[\d+,(\d+)T(\d+),0,[^@]+@,@,,,System\]'

    expression = (r"(?:You (didn't win any|spent|discarded|lost|refined"
          r"|received|sold|placed a bet of|won)|Items? acquired:|(.*) "
          r'(?:has acquired an?|hat eine?n?))'
          r' ([0-9,]+ )?(.*)'
       )
   
    container = Container()
    if cp:
        expression = paste+expression
    else:
        expression = log+expression
    for line in get_logs(location, cp):
        match = re.match(expression, line)
        if match:
            container.add(Loot(cp=cp, *match.groups()))
    return container
            
def get_logs(location, cp=False):
    '''
    Yields lines of each log being parsed.
    Parameters:
        location (str): the location of a pasted log, or the
            location of the first chatlog in a series
        cp (bool): whether the parser should read a single log file
            with the copy-paste syntax rather than the default behavior
            of reading every available log file starting from the given
            one and using the saved-logfile syntax
    Yields:
        (str): each line of each log being parsed
    '''
    if cp:
        with open(location, encoding='utf-8-sig') as f:
            yield from f
    else:
        dirname = os.path.dirname(location)
        basename = os.path.basename(location)
        files = [filename for filename in sorted(os.listdir(dirname)) if
                                                            filename.startswith('Chat_') and
                                                            filename >= basename]
        length = len(files)
        for idx,filename in enumerate(files, start=1):
            print('Processing {} out of {}...'.format(idx, length), end='\r', file=sys.stderr)
            with open(os.path.join(dirname, filename), encoding='utf-8-sig') as f:
                yield from f
        print('\nDone.', file=sys.stderr)
    
class Container:
    '''
    A container that holds Loot objects and has analysis methods.
    Attributes:
        bag (list): stores all the Loot objects
    '''
    def __init__(self):
        self.bag = []
    
    def add(self, loot):
        '''
        Adds a Loot object to the Container's bag.
        Parameter:
            loot (Loot): the Loot object to add to the bag
        '''
        self.bag.append(loot)
    
    def __add__(self, other):
        '''
        Adds two Container objects together.
        Parameter:
            other (Container): the Container to add to this one
        Returns:
            Container: a Container with this one's bag and the other's bag
        '''
        temp = Container()
        temp.bag = self.bag + other.bag
        return temp
    
    def extend(self, other):
        '''
        Adds another Container's bag onto this one's.
        Parameter:
            other (Container): the Container to add to this one
        '''
        self.bag.extend(other.bag)
    
    def __bool__(self):
        '''
        Indicates whether there is anything in the Container's bag.
        Returns:
            bool: whether the bag is non-empty
        '''
        return bool(self.bag)
        
    def __iter__(self):
        '''
        Returns an iterator so we can iterate directly over the Container.
        Returns:
            iter: an iterator for this Container's bag
        '''
        return iter(self.bag)
    
    def get_loot(self, **filters):
        '''
        Yields all the Loot objects that match the given set of filters.
        Example:
            for item in container.get_loot(gain_item='Contraband'):
                print(item)
        Parameter:
            **filters (unpacked dict): the desired filters
        Yields:
            Loot: each matching Loot item
        '''
        extras = {k:filters.pop(k) if k in filters else v
                for k,v in (('item', ''),
                            ('regex', False),
                            ('min_date', min_date), ('max_date', now),
                            ('min_gain', 0), ('max_gain', 10000000000),
                            ('min_loss', 0), ('max_loss', -10000000000))}
        for event in self:
            for k,v in filters.items():
                atr = getattr(event, k)
                if extras['regex']:
                    if isinstance(atr, str) and not re.search(v, atr):
                        success = False
                        break
                elif atr != v and (atr == '' or atr not in v):
                        success = False
                        break
            else:
                success = True
            if extras['item']:
                if extras['regex']:
                    if (not re.search(extras['item'], event.gain_item) and
                    not re.search(extras['item'], event.loss_item)):
                        success = False
                elif ((event.gain_item not in extras['item'] and 
                      event.loss_item not in extras['item']) or
                       (not event.gain_item and event.loss_item not in extras['item']) or
                       (not event.loss_item and event.gain_item not in extras['item'])):
                    success = False
            if (extras['min_date'] <= event.datetime <= extras['max_date']
            ) and (extras['min_gain'] <= event.gain_value <= extras['max_gain']
            ) and (extras['max_loss'] <= event.loss_value <= extras['min_loss']) and success:
                yield event
                
    def get_winners(self, **filters):
        '''
        Yields loot events that were a lockbox win.
        Parameter:
            **filters (unpacked dict): the desired filters
        Yields:
            Loot: each matching Loot item
        '''
        for item in self.get_loot(**filters):
            if item.winner:
                yield item
    
    def average_value_per_event(self, loss=False, **filters):
        '''
        Returns the average value out of all matching loot events.
        Parameters:
            loss (bool): whether we want the losses instead of the default gains
            **filters (unpacked dict): the desired filters
        Returns:
            number: the average value for these loot events
        '''
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
        '''
        Returns the number of events that match the given filters.
        Parameters:
            loss (bool): whether we want the losses instead of the default gains
            **filters (unpacked dict): the desired filters
        Returns:
            int: number of matching loot events for these filters
        '''
        return sum(1 for item in self.get_loot(**filters) if (
                    item.loss_item and loss) or (item.gain_item and not loss))
    
    def total_value(self, loss=False, **filters):
        '''
        Returns the total value of the matching loot events.
        Parameters:
            loss (bool): whether we want the losses instead of the default gains
            **filters (unpacked dict): the desired filters
        Yields:
            int: the total value of these loot events
        '''
        return sum(item.loss_value if loss else item.gain_value for item in
                    self.get_loot(**filters))
    
    def group_by_day(self, UTC=False, **filters):
        '''
        Yields buckets of Loot events separated by day.
        Parameters:
            UTC (bool): whether to separate buckets by local calendar day
                or by UTC calendar day
            **filters (unpacked dict): the desired filters
        Yields:
            tuple (datetime, list): The start date for this bucket and
                the list containing this bucket's Loot objects
        '''
        bucket = []
        loot = iter(self.get_loot(**filters))
        item = next(loot)
        bucket.append(item)
        start_date = item.datetime
        if UTC:
            start_date -= start_date.utcoffset()
        d = start_date.day
        for item in loot:
            if d == ((item.datetime-item.datetime.utcoffset()) if UTC else item.datetime).day:
                bucket.append(item)
            else:
                yield start_date, bucket
                bucket = []
                start_date = item.datetime
                if UTC:
                    start_date -= start_date.utcoffset()
                d = start_date.day
                bucket.append(item)
        if bucket:
            yield start_date, bucket
    
    def totals_by_day(self, sales_loss=False, UTC=False, **filters):
        '''
        Adds up all the events in each daily bucket from group_by_day.
        Parameters:
            sales_loss (bool): whether to show the sold items in the results
            UTC (bool): whether to separate buckets by local calendar day
                or by UTC calendar day
            **filters (unpacked dict): the desired filters
        Yields:
            tuple (datetime, dict, dict): The start date for this bucket,
                a dictionary of gain loot events and their values, and
                a dictionary of loss loot events and their values
        '''
        for d, bucket in self.group_by_day(UTC=UTC, **filters):
            gains = {}
            losses = {}
            for item in bucket:
                gains[item.gain_item] = gains.get(item.gain_item, 0) + item.gain_value
                if not item.gain_item or sales_loss:
                    losses[item.loss_item] = losses.get(item.loss_item, 0) + item.loss_value
            if '' in gains:
                gains.pop('')
            if '' in losses:
                losses.pop('')
            yield d, gains, losses
    
    def cumulative_totals(self, sales_loss=False, UTC=False, **filters):
        '''
        Yields the cumulative totals for each successive daily bucket from totals_by_day.
        Parameters:
            sales_loss (bool): whether to show the sold items in the results
            UTC (bool): whether to separate buckets by local calendar day
                or by UTC calendar day
            **filters (unpacked dict): the desired filters
        Yields:
            tuple (datetime, Counter): The start date for this bucket, and
                a Counter holding the current cumulative total
        '''
        count = collections.Counter()
        for d, gains, losses in self.totals_by_day(UTC=UTC, **filters):
            count.update(gains)
            count.update(losses)
            yield d, count
    
    def average_totals(self, sales_loss=False, UTC=False, **filters):
        '''
        Returns a dictionary with the average daily value for each matching item.
        Parameters:
            sales_loss (bool): whether to show the sold items in the results
            UTC (bool): whether to separate buckets by local calendar day
                or by UTC calendar day
            **filters (unpacked dict): the desired filters
        Returns:
            dict: the matching items with their average daily value
        '''
        length = 0
        for d, count in self.cumulative_totals(UTC=UTC, **filters):
            length += 1
        if length:
            return {k:v//length for k,v in count.items()}
        else:
            return {'None':0}
    
    def counter(self, **filters):
        '''
        Returns a Counter with the number of times each loot item appeared.
        Parameter:
            **filters (unpacked dict): the desired filters
        Returns:
            Counter: each item with their number of appearances
        '''
        return collections.Counter(val for item in self.get_loot(**filters)
                                    for val in (item.loss_item, item.gain_item) if val)
        
    def common(self, least=False, counter=None, **filters):
        '''
        Returns the most or least common item, by number of loot events.
        Parameters:
            least (bool): get the least common item, rather than the default most
            counter (Counter): send a Counter object to avoid having to make it again
            **filters (unpacked dict): the desired filters
        Returns:
            str: the most or least common item, by number of loot events
        '''
        if counter:
            return counter.most_common()[-1*least]
        return self.counter(**filters).most_common()[-1*least]
    
    def dabo(self, **filters):
        '''
        Returns a zip object with Dabo gambling losses and gains.
        Parameter:
            **filters (unpacked dict): the desired filters
        Returns:
            zip: Each loss and its corresponding gain for Dabo gambling
        '''
        filters['interaction'] = {"didn't win any", 'placed a bet of', 'won'}
        gained = []
        lost = []
        for item in self.get_loot(**filters):
            if item.gain_item:
                gained.append(item)
            else:
                lost.append(item)
        return zip(lost, gained)
    
    def __str__(self):
        return '\n'.join(str(item) for item in self)
    
    def __repr__(self):
        return str(self)

class Loot:
    def __init__(self, d, t, interaction, winner, quantity, item, cp=False):
        if cp:
            if d:
                month, day = map(int, d.strip('[] ').split('/'))
            else:
                month, day = 1,1
            if t:
                hour, minute = map(int, t.strip('[] ').split(':'))
            else:
                hour, minute = 0, 0
            if tzlocal_present:
                self.datetime = tzlocal.get_localzone().localize(
                    datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute))
            else:
                self.datetime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        else:
            if tzlocal_present:
                #self.datetime = tzlocal.get_localzone().localize(datetime.datetime.strptime(d+t, '%Y%m%d%H%M%S'))
                self.datetime = tzlocal.get_localzone().localize(datetime.datetime(year=int(d[:4]), month=int(d[4:6]),
                    day=int(d[6:]), hour=int(t[:2]), minute=int(t[2:4]), second=int(t[4:])))
            else:
                #self.datetime = datetime.datetime.strptime(d+t, '%Y%m%d%H%M%S')
                self.datetime = datetime.datetime(year=int(d[:4]), month=int(d[4:6]),
                    day=int(d[6:]), hour=int(t[:2]), minute=int(t[2:4]), second=int(t[4:]))
        
        self.winner = winner or ''
        
        quantity = quantity or ''
        quantity = (int(quantity.strip().replace(',','') or 0) or
                         int(''.join(item.split(' x ')[1:]).replace(',','') or 1))
        
        item = item.split(' x ')[0].rstrip('!.').rsplit(' erhalten', maxsplit=1)[0]
        
        self.interaction = interaction or ''
        
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

if __name__ == '__main__':
                
    pasted = '*cp' in sys.argv
    container = container_from_logs(location=sys.argv[1], cp=pasted)
    item_filter = {'Dilithium', 'Dilithium Ore', 'Refined Dilithium',
               'Contraband', 'Energy Credits', 'Gold-Pressed Latinum'}
    
    print('Daily averages:')
    print('Item', 'Average value per day', sep='\t')
    for item in container.average_totals(item=item_filter).items():
        print(*item, sep='\t')
    
    print('\nTotals per day:')
    headers = set()
    results = []
    for d,g,l in container.totals_by_day(item=item_filter):
        result = collections.Counter(g)
        result.update(l)
        results.append((datetime.datetime.strftime(d, '%Y-%m-%d'), result))
        headers |= set(result)
    headers = sorted(headers)
    print('Date', *headers, sep='\t')
    for d,c in results:
        print(d, *map(c.get, headers), sep='\t')
    
    print('\nDabo gambling results:')
    print('Bet', 'Won', sep='\t')
    for l,g in container.dabo():
        print(l.loss_value, g.gain_value, sep='\t')
    
    print('\nLockbox ship winners:')
    print('Date', 'Winner', 'Item', sep='\t')
    for item in container.get_winners():
        try:
            print(item.datetime, item.winner, item.gain_item, sep='\t')
        except UnicodeEncodeError:
            print('Character not available. Try redirecting to a file.')
