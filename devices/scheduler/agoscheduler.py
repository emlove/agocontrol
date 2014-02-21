#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IPX800 relay board client
# http://gce-electronics.com
# copyright (c) 2013 tang
 
import sys
import os
import agoclient
import threading
import time
import logging
import json
import copy

from dateutil.relativedelta import *
from dateutil.rrule import *
from dateutil.parser import *
from datetime import datetime

from qpid.datatypes import uuid4
from bisect import bisect_left, bisect_right
from operator import itemgetter

client = None
allSchedules = None #(scheduleid, schedule)
timeSchedules = None #(timestamp, scheduleid)
scenarioControllerUuid = None

#logging.basicConfig(filename='agosqueezebox.log', level=logging.INFO, format="%(asctime)s %(levelname)s : %(message)s")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s : %(message)s")

#=================================
#classes
#=================================
class SortedCollection(object):
    """SortedCollection from http://code.activestate.com/recipes/577197-sortedcollection/"""
    def __init__(self, iterable=(), key=None):
        self._given_key = key
        key = (lambda x: x) if key is None else key
        decorated = sorted((key(item), item) for item in iterable)
        self._keys = [k for k, item in decorated]
        self._items = [item for k, item in decorated]
        self._key = key

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, 'key function')

    def clear(self):
        self.__init__([], self._key)

    def copy(self):
        return self.__class__(self, self._key)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        if isinstance( i,slice ):
            sc = self.__class__( key=self._key )
            sc._keys  = self._keys[i]
            sc._items = self._items[i]
            return sc
        else:
            return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r, key=%s)' % (
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, '__name__', repr(self._given_key))
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, item):
        'Return first item with a key == k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, item)
        if i != len(self) and self._keys[i] == item:
            return i
        raise ValueError('No item found with key equal to: %r' % (item,))

    def index_le(self, k):
        'Return last index with a key <= k.  Raise ValueError if not found.'
        i = bisect_right(self._keys, k)
        if i:
            return i-1
        raise ValueError('No index found with key at or below: %r' % (k,))

    def index_lt(self, k):
        'Return last index with a key < k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i:
            return i-1
        raise ValueError('No index found with key below: %r' % (k,))

    def index_ge(self, k):
        'Return first index with a key >= equal to k.  Raise ValueError if not found'
        i = bisect_left(self._keys, k)
        if i != len(self):
            return i
        raise ValueError('No index found with key at or above: %r' % (k,))

    def index_gt(self, k):
        'Return first index with a key > k.  Raise ValueError if not found'
        i = bisect_right(self._keys, k)
        if i != len(self):
            return i
        raise ValueError('No index found with key above: %r' % (k,))

    def count(self, item):
        'Return number of occurrences of item'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].count(item)

    def insert(self, item):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def insert_right(self, item):
        'Insert a new item.  If equal keys are found, add to the right'
        k = self._key(item)
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        'Remove first occurence of item.  Raise ValueError if not found'
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def find(self, k):
        'Return first item with a key == k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError('No item found with key equal to: %r' % (k,))

    def find_all(self, k, getter=None):
        'Find all items with specified key. If getter specified, return values'
        out = []
        try:
            i = self.index(k)
            if getter:
                out.append(getter(self._items[i]))
            else:
                out.append(self._items[i])
            i += 1
            while i<len(self) and self._keys[i]==k:
                if getter:
                    out.append(getter(self._items[i]))
                else:
                    out.append(self._items[i])
                i += 1
        except ValueError:
            pass
        return out

    def find_le(self, k):
        'Return last item with a key <= k.  Raise ValueError if not found.'
        i = bisect_right(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key at or below: %r' % (k,))

    def find_lt(self, k):
        'Return last item with a key < k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key below: %r' % (k,))

    def find_ge(self, k):
        'Return first item with a key >= equal to k.  Raise ValueError if not found'
        i = bisect_left(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key at or above: %r' % (k,))

    def find_gt(self, k):
        'Return first item with a key > k.  Raise ValueError if not found'
        i = bisect_right(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key above: %r' % (k,))

    def get_ge_le(self, ge, le):
        'Return sorted collection in range ge<=items<=le'
        items = self._items[self.index_ge(ge):self.index_le(le)+1]
        sc = self.__class__(items, key=self._key)
        return sc

    def get_values(self, getter):
        'Return map of items values according to specified getter function'
        return map(getter, self._items)

#=================================
#utils
#=================================
def quit(msg):
    """Exit application"""
    global client
    if client:
        del client
        client = None
    logging.fatal(msg)
    sys.exit(0)

def checkContent(content, params):
    """Check if all params are in content"""
    for param in params:
        if not content.has_key(param):
            return False
    return True

def momentjsToPython(momentjsDatetime):
    """convert momentjs datetime to python datetime
       format: 2014-02-11T09:00:00+01:00"""
    return parse(momentjsDatetime)

def pythonToMomentjs(dt):
    """Convert python datetime with tzinfo to momentjs datetime"""
    if datetime.tzinfo==None:
        raise Exception("No timezone info on datetime.")
    out = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return out[:len(out)-2]+':'+out[len(out)-2:]

def calendarToPython(fullCalendarDatetime):
    """convert fullcalendar v1 UTC datetime to python datetime"""
    return parse(fullCalendarDatetime)

def createSchedule(title, uuidStart, uuidEnd, dateStart, dateEnd, color, repeat):
    """create schedule structure
       @see http://arshaw.com/fullcalendar/docs2/event_data/Event_Object/"""
    return {
        'id': str(uuid4()),
        'title': title,
        'start': dateStart,
        'end': dateEnd,
        'color': color,
        'uuidStart': uuidStart,
        'uuidEnd': uuidEnd,
        'repeat': repeat,
        'allDay': 0
    }

def saveSchedules():
    """save schedules to config file"""
    global allSchedules
    if not agoclient.setConfigOption('agoscheduler', 'all', json.dumps(allSchedules.get_values(itemgetter(1)))):
        logging.exception('Unable to load config file')

def loadSchedules():
    """load schedules from config file"""
    global allSchedules, timeSchedules
    #create members
    allSchedules = SortedCollection([], itemgetter(0))
    timeSchedules = SortedCollection([], itemgetter(0))
    #get schedules from confif file
    schedules = agoclient.getConfigOption("agoscheduler", "all", "[]")
    schedules = json.loads(schedules)
    #and store them in sorted collection
    for schedule in schedules:
        addSchedule(schedule)
    logging.info('Loaded %d schedules' % len(allSchedules))

def computeRecurrings(firstRecurringDatetime, repeat):
    """Compute recurring datetimes according to repeat value"""
    #get tzinfo
    tzinfo = firstRecurringDatetime.tzinfo
    #create new datetime without tzinfo (mandatory to use dateutil.rrule lib:S)
    dt = datetime(firstRecurringDatetime.year, firstRecurringDatetime.month, firstRecurringDatetime.day, firstRecurringDatetime.hour, firstRecurringDatetime.minute)
    #get current date infos
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    until = today + relativedelta(months=+1)
    #compute reccurings
    recurrings = []
    if repeat==0:
        #not a recurring schedule
        recurrings = [dt]
    elif repeat==1:
        #repeat every day
        recurrings = list(rrule(DAILY, until=until, dtstart=dt))
    elif repeat==7:
        #repeat every week
        recurrings = list(rrule(WEEKLY, until=until, dtstart=dt))
    elif repeat==31:
        #repeat every month
        recurrings = list(rrule(MONTHLY, until=until, dtstart=dt))
    elif repeat==365:
        #repeat every year
        #need to save at least 2 schedules, otherwise it will be lost by purge
        until = today + relativedelta(years=+1, months=+1)
        recurrings = list(rrule(YEARLY, until=until, dtstart=dt))
    #read tzinfo to computed recurrings
    fixedRecurrings = []
    for recurring in recurrings:
        fixedRecurrings.append(datetime(recurring.year, recurring.month, recurring.day, recurring.hour, recurring.minute, 0, 0, tzinfo))
    return fixedRecurrings

def addSchedule(schedule, computeRecurring=False):
    """add schedule. /!\ Need to catch Exception
       @info: datetime are internally stored in UTC"""
    addedSchedules = []
    recurringsStart = None
    recurringsEnd = None
    if computeRecurring:
        #add recurring schedules for next 6 monthes only
        #compute recurring datetimes
        scheduleStart = calendarToPython(schedule['start'])
        scheduleEnd = calendarToPython(schedule['end'])
        recurringsStart = computeRecurrings(scheduleStart, int(schedule['repeat']))
        recurringsEnd = computeRecurrings(scheduleEnd, int(schedule['repeat']))
    else:
        recurringsStart = [momentjsToPython(schedule['start'])]
        recurringsEnd = [momentjsToPython(schedule['end'])]

    #check recurring lists content
    if len(recurringsStart)!=len(recurringsEnd):
        raise Exception("Recurring lists content is not equal! len(start)=%d len(end)=%d" % (len(recurringStart), len(recurringEnd)))

    #save start scenario timestamp in timeSchedules list
    for i in range(len(recurringsStart)):
        #save schedule in allSchedules list
        newSchedule = copy.copy(schedule)
        newSchedule['start'] = pythonToMomentjs(recurringsStart[i])
        newSchedule['end'] = pythonToMomentjs(recurringsEnd[i])
        allSchedules.insert( (newSchedule['id'], newSchedule) )
        addedSchedules.append(newSchedule)

        #key = int(momentjsToPython(schedule['start']).strftime('%s'))
        key = int(recurringsStart[i].strftime('%s'))
        timeSchedules.insert( (key, {'id':newSchedule['id'], 'scenario':newSchedule['uuidStart']}) )

        #save end scenario timestamp in timeSchedules list
        if schedule['uuidEnd']!='0':
            #key = int(momentjsToPython(schedule['end']).strftime('%s'))
            key = int(recurringsEnd[i].strftime('%s'))
            timeSchedules.insert( (key, {'id':newSchedule['id'], 'scenario':newSchedule['uuidEnd']}) )
    return addedSchedules

def delSchedule(scheduleId):
    """delete schedule. /!\ Need to catch Exception"""
    #search schedules to delete from allSchedules list
    schedsToDel = allSchedules.find_all(scheduleId)
    delCount = 0
    for schedToDel in schedsToDel:
        #remove start scenario timestamp from timeSchedules list
        dateStart = int(momentjsToPython(schedToDel[1]['start']).strftime('%s'))
        scheds = timeSchedules.find_all(dateStart)
        for sched in scheds:
            if sched[1]['id']==scheduleId:
                timeSchedules.remove(sched[0])
                break
        #remove end scenario timestamp from timeSchedules list
        dateEnd = int(momentjsToPython(schedToDel[1]['end']).strftime('%s'))
        scheds = timeSchedules.find_all(dateEnd)
        for sched in scheds:
            if sched[1]['id']==scheduleId:
                timeSchedules.remove(sched[0])
                break
        #and finally delete schedule from allSchedules list
        allSchedules.remove(scheduleId)
        delCount += 1
    logging.info("%d schedules deleted" % delCount)

def updSchedule(schedule, infos):
    """update schedule. /!\ Need to catch Exception"""
    updCount = 0
    #check fields to update
    updateStartDate = 0
    if infos['type']=='drop':
        #compute time difference in minutes
        updateStartDate = infos['days']*1440 + infos['minutes']
    updateEndDate = 0
    if infos['type']=='drop' or infos['type']=='resize':
        #compute time difference in minutes
        updateEndDate = infos['days']*1440 + infos['minutes']
    removeEndSchedule = False
    if schedule['uuidEnd']=='0':
        removeEndSchedule = True
    #get schedules to update
    schedsToUpd = allSchedules.find_all(schedule['id'])
    for schedToUpd in schedsToUpd:
        #compute new start
        start = momentjsToPython(schedToUpd[1]['start'])
        start = start + relativedelta(minutes=updateStartDate)
        #compute new end
        end = momentjsToPython(schedToUpd[1]['end'])
        end = end + relativedelta(minutes=updateEndDate)

        if updateStartDate!=0:
            #start date changed
            dateStart = int(momentjsToPython(schedToUpd[1]['start']).strftime('%s'))
            scheds = timeSchedules.find_all(dateStart)
            for sched in scheds:
                if sched[1]['id']==schedToUpd[1]['id']:
                    #remove old entry
                    timeSchedules.remove(sched[0])
                    #compute new start
                    key = int(start.strftime('%s'))
                    #and insert new schedule time
                    timeSchedules.insert( (key, {'id':schedule['id'], 'scenario':schedule['uuidStart']}) )
                    #and update start in allSchedules list
        if updateEndDate!=0:
            #end date changed
            dateEnd = int(momentjsToPython(schedToUpd[1]['end']).strftime('%s'))
            scheds = timeSchedules.find_all(dateEnd)
            for sched in scheds:
                if sched[1]['id']==schedToUpd[1]['id']:
                    #remove old entry
                    timeSchedules.remove(sched[0])
                    #compute new start
                    key = int(end.strftime('%s'))
                    #insert new schedule time
                    timeSchedules.insert( (key, {'id':schedule['id'], 'scenario':schedule['uuidEnd']}) )
                    #and update end in allSchedules list
        if removeEndSchedule:
            #no end scenario, remove all schedules
            dateEnd = int(momentjsToPython(schedToUpd[1]['end']).strftime('%s'))
            scheds = timeSchedules.find_all(dateEnd)
            for sched in scheds:
                if sched[1]['id']==schedToUpd[1]['id']:
                    #remove old entry
                    timeSchedules.remove(sched[0])              
        #update schedule
        schedToUpd[1]['title'] = schedule['title']
        schedToUpd[1]['uuidStart'] = schedule['uuidStart']
        schedToUpd[1]['uuidEnd'] = schedule['uuidEnd']
        schedToUpd[1]['color'] = schedule['color']
        schedToUpd[1]['start'] = pythonToMomentjs(start)
        schedToUpd[1]['end'] = pythonToMomentjs(end)
        updCount += 1
    logging.info("%d schedules updated" % updCount)

#=================================
#functions
#=================================
def commandHandler(internalid, content):
    """ago command handler"""
    logging.info('commandHandler: %s, %s' % (internalid,content))
    global client, allSchedules
    command = None

    if content.has_key('command'):
        command = content['command']
    else:
        logging.error('No command specified')
        return None

    if internalid=='agoscheduler':
        if command=='addSchedule':
            #add new schedule
            scheds = None
            if checkContent(content, ['title', 'uuidStart', 'uuidEnd', 'dateStart', 'dateEnd', 'color', 'repeat']):
                try:
                    #create new schedule
                    sched = createSchedule(content['title'], content['uuidStart'], content['uuidEnd'], content['dateStart'], content['dateEnd'], content['color'], content['repeat'])
                    #add schedule
                    scheds = addSchedule(sched, True)
                    logging.info("%d schedules added" % len(scheds))
                    #save updates
                    saveSchedules()
                except:
                    logging.exception('Unable to add new schedule:')
                    return {'error':1, 'msg':'Internal error'}
            else:
                logging.error("Command addSchedule: parameter missing")
                return {'error':1, 'msg':'Internal error'}
            return {'error':0, 'msg':'', 'schedules':scheds}

        elif command=='delSchedule':
            #delete schedule
            if checkContent(content, ['id']):
                try:
                    #delete schedule
                    delSchedule(content['id'])
                    #and save updates
                    saveSchedules()
                except ValueError:
                    logging.exception('Unable to delete schedule:')
                    return {'error':1, 'msg':'Internal error'}
            else:
                logging.error('Command delSchedule: parameter missing')
                return {'error':1, 'msg':'Internal error'}
            return {'error':0, 'msg':''}

        elif command=='updSchedule':
            #update schedule
            #if checkContent(content, ['id', 'title', 'uuidStart', 'uuidEnd', 'dateStart', 'dateEnd', 'color', 'repeat']):
            if checkContent(content, ['schedule', 'infos']):
                #infos format:
                # type: drop, resize, update
                # days: offset days
                # minutes: offset minutes
                try:
                    #update schedule
                    updSchedule(content['schedule'], content['infos'])
                    #and save updates
                    saveSchedules()
                except ValueError:
                    #not found
                    logging.exception('Unable to update schedule:')
                    return {'error':1, 'msg':'Internal error'}
            else:
                logging.error('Command updSchedule: parameter missing')
                return {'error':1, 'msg':'Internal error'}
            return {'error':0, 'msg':''}

        elif command=='getSchedules':
            #return all schedules
            return {'error':0, 'msg':'', 'schedules':allSchedules.get_values(itemgetter(1))}
            

def eventHandler(event, content):
    """ago event handler"""
    #logging.info('eventHandler: %s, %s' % (event, content))
    global client, timeSchedules

    if event=='event.environment.timechanged':
        try:
            #format: {u'hour': 15, u'month': 2, u'second': 0, u'weekday': 6, u'year': 2014, u'yday': 46, u'day': 15, u'minute': 37}
            #convert received datetime to timestamp
            currentDt = datetime(content['year'], content['month'], content['day'], content['hour'], content['minute'], 0)
            currentTs = int(currentDt.strftime('%s'))
            #search scenarios to execute
            schedules = timeSchedules.find_all(currentTs, itemgetter(1))
            #execute scenarios
            for schedule in schedules:
                logging.info('Execute scenario id "%s"' % schedule['scenario'])
                client.sendMessage({'uuid':scenarioControllerUuid, 'command':'run', 'internalid':schedule['scenario']})
        except:
            logging.exception('Exception on timechanged event:')


#=================================
#main
#=================================
#init
try:
    #connect agoclient
    client = agoclient.AgoConnection('agoscheduler')

    #members
    loadSchedules()

    #add client handlers
    client.addHandler(commandHandler)
    client.addEventHandler(eventHandler)

    #add controller
    client.addDevice('agoscheduler', 'agoscheduler')

    #get scenariocontroller uuid (don't catch exceptions because no uuid no scenario execution)
    inventory = client.getInventory()
    for uuid in inventory.content['devices']:
        if inventory.content['devices'][uuid]['devicetype']=='scenariocontroller':
            scenarioControllerUuid = uuid
            break
    if not scenarioControllerUuid:
        raise Exception('scenariocontroller uuid not found!')

except Exception as e:
    #init failed
    logging.exception("Exception on init")
    quit('Init failed, exit now.')

#run agoclient
try:
    logging.info('Running agoscheduler...')
    client.run()
except KeyboardInterrupt:
    #stopped by user
    quit('agoscheduler stopped by user')
except Exception as e:
    logging.exception("Exception on main:")
    #stop everything
    quit('agoscheduler stopped')

