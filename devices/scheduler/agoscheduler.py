#!/usr/bin/env python
# -*- coding: utf-8 -*-

# agoscheduler
# copyright (c) 2014 tang (tanguy.bonneau@gmail.com) 
 
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
nowUtc = None

#logging.basicConfig(filename='/opt/agocontrol/agoscheduler.log', level=logging.INFO, format="%(asctime)s %(levelname)s : %(message)s")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s : %(message)s")

#=================================
#classes
#=================================
class SortedCollection(object):
    """constants"""
    LEFT = 0
    RIGHT = 1

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

    def insert(self, item, direction=LEFT):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(item)
        if direction==SortedCollection.LEFT:
            i = bisect_left(self._keys, k)
        else:
            i = bisect_right(self._keys, k)
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

    def removeIndex(self, index):
        'Remove item at specified index'
        del self._keys[index]
        del self._items[index]

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

    def find_range(self, low, high):
        'Return sorted collection in range low<=items<=high'
        items = self._items[self.index_ge(low):self.index_le(high)+1]
        sc = self.__class__(items, key=self._key)
        return sc

    def get_values(self, getter):
        'Return map of items values according to specified getter function'
        return map(getter, self._items)

    def get_keys(self):
        'Return map of keys according to specified getter function'
        return self._keys

    def get(self, index):
        return self._items[index]


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

def getScenarioControllerUuid():
    """get scenariocontroller uuid"""
    global client, scenarioControllerUuid
    inventory = client.getInventory()
    for uuid in inventory.content['devices']:
        if inventory.content['devices'][uuid]['devicetype']=='scenariocontroller':
            scenarioControllerUuid = uuid
            break
    if not scenarioControllerUuid:
        raise Exception('scenariocontroller uuid not found!')


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
    if dt.tzinfo==None:
        raise Exception("No timezone info on datetime.")
    out = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return out[:len(out)-2]+':'+out[len(out)-2:]

def calendarToPython(fullCalendarDatetime):
    """convert fullcalendar UTC datetime to python datetime"""
    return parse(fullCalendarDatetime)

def pythonToCalendar(pythonDatetime):
    """convert python datetime to fullcalendar UTC datetime
       format: 2014-02-26T12:00:00.000Z"""
    return pythonDatetime.strftime("%Y-%m-%dT%H:%M:%SZ")

def createSchedule(title, uuidStart, uuidEnd, dateStart, dateEnd, color, repeat):
    """create schedule structure
       @see http://arshaw.com/fullcalendar/docs/event_data/Event_Object/"""
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
        addSchedule(schedule, False, False)
    logging.info('Loaded %d schedules' % len(allSchedules))

def computeRecurrings(recurringDatetime, repeat, months):
    global nowUtc
    #get tzinfo
    tzinfo = recurringDatetime.tzinfo
    #create start datetime (without tzinfo because its mandatory to use dateutil.rrule lib:S)
    start = datetime(recurringDatetime.year, recurringDatetime.month, recurringDatetime.day, recurringDatetime.hour, recurringDatetime.minute)
    #compute current datetime
    eoy = datetime(nowUtc.year, 12, 31) #end of year
    #compute reccurings
    recurrings = []
    if repeat==0:
        #not a recurring schedule
        recurrings = [start]
    elif repeat==1:
        #repeat every day
        recurrings = list(rrule(DAILY, bymonth=months, until=eoy, dtstart=start))
    elif repeat==7:
        #repeat every week
        recurrings = list(rrule(WEEKLY, bymonth=months, until=eoy, dtstart=start))
    elif repeat==31:
        #repeat every month
        recurrings = list(rrule(MONTHLY, bymonth=months, until=eoy, dtstart=start))
    elif repeat==365:
        #repeat every year
        #need to save at least 2 schedules, otherwise it will be lost by purge
        until = start + relativedelta(years=+1, months=+1)
        recurrings = list(rrule(YEARLY, until=until, dtstart=start))
    #re-add tzinfo
    for recurring in recurrings:
        recurring.replace(tzinfo=tzinfo)
    return recurrings

def addSchedule(schedule, computeRecurring=False, append=False):
    """add schedule. /!\ Need to catch Exception
       @param schedule: schedule to add
       @param computeRecurring: compute recurring schedules too
       @param append: append new recurring schedules 
       @info: datetime are internally stored in UTC"""
    global nowUtc
    addedSchedules = []
    recurringsStart = None
    recurringsEnd = None
    if computeRecurring:
        #compute recurring datetimes
        scheduleStart = calendarToPython(schedule['start'])
        scheduleEnd = calendarToPython(schedule['end'])
        if not append:
            #compute schedules to now until end of next month
            recurringsStart = computeRecurrings(scheduleStart, int(schedule['repeat']), [nowUtc.month, nowUtc.month+1])
            recurringsEnd = computeRecurrings(scheduleEnd, int(schedule['repeat']), [nowUtc.month, nowUtc.month+1])
        else:
            #compute schedules for next month
            recurringsStart = computeRecurrings(scheduleStart, int(schedule['repeat']), [nowUtc.month+1])
            recurringsEnd = computeRecurrings(scheduleEnd, int(schedule['repeat']), [nowUtc.month+1])
        logging.debug("addSchedule: schedule=%s computeReccuring=%s append=%s" % (str(schedule), str(computeRecurring), str(append)))
        logging.debug(recurringsStart)
        logging.debug(recurringsEnd)
    else:
        recurringsStart = [calendarToPython(schedule['start'])]
        recurringsEnd = [calendarToPython(schedule['end'])]

    #check recurring lists content
    if len(recurringsStart)!=len(recurringsEnd):
        raise Exception("Recurring lists content is not equal! len(start)=%d len(end)=%d" % (len(recurringsStart), len(recurringsEnd)))

    #save start scenario timestamp in timeSchedules list
    for i in range(len(recurringsStart)):
        #save schedule in allSchedules list
        newSchedule = copy.copy(schedule)
        newSchedule['start'] = pythonToCalendar(recurringsStart[i])
        newSchedule['end'] = pythonToCalendar(recurringsEnd[i])
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

def purgeSchedule(schedule):
    """purge specified schedule and nothing else (don't touch on recurring schedules)"""
    global allSchedules, timeSchedules
    found = False
    for i in range(len(allSchedules)):
        if allSchedules[i][1]['id']==schedule['id'] and allSchedules[i][1]['start']==schedule['start'] and allSchedules[i][1]['end']==schedule['end']:
            allSchedules.removeIndex(i)
            found = True
            break
    logging.warning('PurgeSchedule: schedule %s not found in allSchedules list' % str(schedule))
    found = False
    for i in range(len(timeSchedules)):
        if timeSchedules[i][1]['id']==schedule['id'] and timeSchedules[i][1]['scenario']==schedule['uuidStart']:
            timeSchedules.removeIndex(i)
            found = True
            break
    logging.warning('PurgeSchedule: schedule %s not found in timeSchedules list (uuidStart)' % str(schedule))
    if schedule['uuidEnd']!='0':
        found = False
        for i in range(len(timeSchedules)):
            if timeSchedules[i][1]['id']==schedule['id'] and timeSchedules[i][1]['scenario']==schedule['uuidEnd']:
                timeSchedules.removeIndex(i)
                found = True
                break
        logging.warning('PurgeSchedule: schedule %s not found in timeSchedules list (uuidEnd)' % str(schedule))

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
                    scheds = addSchedule(sched, True, False)
                    logging.info("%d schedules added" % len(scheds))
                    #save updates
                    saveSchedules()
                except:
                    logging.exception('Unable to add new schedule:')
                    return {'error':1, 'msg':'#ie'}
            else:
                logging.error("Command addSchedule: parameter missing")
                return {'error':1, 'msg':'#ie'}
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
                    return {'error':1, 'msg':'#ie'}
            else:
                logging.error('Command delSchedule: parameter missing')
                return {'error':1, 'msg':'#ie'}
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
                    logging.info(allSchedules)
                    logging.info(timeSchedules)
                except ValueError:
                    #not found
                    logging.exception('Unable to update schedule:')
                    return {'error':1, 'msg':'#ie'}
            else:
                logging.error('Command updSchedule: parameter missing')
                return {'error':1, 'msg':'#ie'}
            return {'error':0, 'msg':''}

        elif command=='getSchedules':
            #return all schedules
            return {'error':0, 'msg':'', 'schedules':allSchedules.get_values(itemgetter(1))}
            

def eventHandler(event, content):
    """ago event handler"""
    #logging.info('eventHandler: %s, %s' % (event, content))
    global client, timeSchedules, nowUtc

    if event=='event.environment.timechanged':
        try:
            #format: {u'hour': 15, u'month': 2, u'second': 0, u'weekday': 6, u'year': 2014, u'yday': 46, u'day': 15, u'minute': 37}
            #convert received datetime to timestamp UTC
            currentDtLocal = datetime(content['year'], content['month'], content['day'], content['hour'], content['minute'], 0)
            currentTsLocal = int(currentDtLocal.strftime('%s'))
            currentTsUtc = int(time.mktime(time.gmtime(time.mktime(currentDtLocal.timetuple()))))
            currentDtUtc = datetime.fromtimestamp(currentTsUtc)

            #search scenarios to execute
            schedules = timeSchedules.find_all(currentTsUtc, itemgetter(1))

            #get scenario controller uuid
            if not scenarioControllerUuid:
                getScenarioControllerUuid()

            #execute scenarios
            for schedule in schedules:
                logging.info('Execute scenario id "%s"' % schedule['scenario'])
                client.sendMessage(None, {'uuid':scenarioControllerUuid, 'command':'run', 'internalid':schedule['scenario']})

            #each new year append yearly recurring schedules
            if currentDtLocal.year!=nowUtc.year:
                for schedule in allSchedules:
                    if schedule[1]['repeat']=='365':
                        addSchedule(schedule[1], True, True)
            
            #each months purge executed schedules and append existing recurring schedules automatically
            if currentDtLocal.month!=nowUtc.month:
                #purge old schedules
                try:
                    startTsUtc = int((nowUtc + relativedelta(months=-1)).strftime('%s'))
                    doneSchedules = timeSchedules.find_range(startTsUtc, currentTsUtc)
                    for doneSchedule in doneSchedules:
                        purgeSchedule(doneSchedule[1])
                    logging.info('Monthly purge removed %d schedules' % len(doneSchedules))
                except:
                    logging.exception('Monthly schedulings purge failed:')

                #add new recurring schedules for next month
                try:
                    #get schedules in current month
                    endTsUtc = int((currentDtUtc + relativedelta(months=+1)).strftime('%s'))
                    monthSchedules = timeSchedules.find_range(currentTsUtc, endTsUtc)
                    #filter recurrings to keep only first occurence
                    updSchedules = []
                    for monthSchedule in monthSchedules:
                        if updSchedules.count(monthSchedule[1]['id'])==0:
                            updSchedules.append(monthSchedule[1]['id'])
                    #append new schedules for next month
                    for updSchedule in updSchedules:
                        schedule = allSchedules.find(updSchedule)
                        logging.info(schedule)
                        if schedule[1]['repeat']!='0':
                            addSchedule(schedule[1], True, True)
                except ValueError:
                    #no schedules found
                    logging.info('No recurring schedules to append')
                    pass
        except:
            logging.exception('Exception on timechanged event:')

    #update current datetime
    nowUtc = datetime.utcnow()


#=================================
#main
#=================================
#init
try:
    #update current datetime
    nowUtc = datetime.utcnow()

    #connect agoclient
    client = agoclient.AgoConnection('agoscheduler')

    #members
    loadSchedules()

    #add client handlers
    client.addHandler(commandHandler)
    client.addEventHandler(eventHandler)

    #add controller
    client.addDevice('agoscheduler', 'agoscheduler')

except Exception as e:
    #init failed
    logging.exception("Exception on init")
    quit('Init failed, exit now.')


#Unitary tests
"""
def calDt(string):
    return string % (nowUtc.year, nowUtc.month, nowUtc.day)
repeat_no = createSchedule('test_repeatno'      , '1234-1234-1234', '0', calDt('%s-%s-%sT12:00:00.000Z'), calDt('%s-%s-%sT12:30:00.000Z'), '#FF0000', '0')
repeat_day = createSchedule('test_repeatday'    , '1234-1234-1234', '0', calDt('%s-%s-%sT13:00:00.000Z'), calDt('%s-%s-%sT13:30:00.000Z'), '#FF0000', '1')
repeat_week = createSchedule('test_repeatweek'  , '1234-1234-1234', '0', calDt('%s-%s-%sT14:00:00.000Z'), calDt('%s-%s-%sT14:30:00.000Z'), '#FF0000', '7')
repeat_month = createSchedule('test_repeatmonth', '1234-1234-1234', '0', calDt('%s-%s-%sT15:00:00.000Z'), calDt('%s-%s-%sT15:30:00.000Z'), '#FF0000', '31')
repeat_year = createSchedule('test_repeatyear'  , '1234-1234-1234', '0', calDt('%s-%s-%sT16:00:00.000Z'), calDt('%s-%s-%sT16:30:00.000Z'), '#FF0000', '365')
####################################
#CHANGE HERE SCHEDULES TO TEST (NO, DAY, WEEK, MONTH, YEAR)
addSchedule(repeat_year, True, False)
####################################
"""
"""
logging.info('----------Add schedules----------')
for sched in allSchedules:
    logging.info(sched[1])
#force now datetime to 1st of next month to simulate schedules appending
nowUtc = datetime(nowUtc.year, nowUtc.month, 1, 0, 0, 0)
currentTsUtc = int(nowUtc.strftime('%s'))
currentDtUtc = datetime.fromtimestamp(currentTsUtc)
endTsUtc = int((currentDtUtc + relativedelta(months=+1, days=-1)).strftime('%s'))
endDtUtc = datetime.fromtimestamp(endTsUtc)
logging.info('current=%s end=%s' % (str(currentTsUtc), str(endTsUtc)))
logging.info('current=%s end=%s' % (str(currentDtUtc), str(endDtUtc)))
monthSchedules = []
logging.info('----------Schedules in range [%s-%s]----------' % (str(currentDtUtc), str(endDtUtc)))
try:
    monthSchedules = timeSchedules.find_range(currentTsUtc, endTsUtc)
    for sched in monthSchedules:
        logging.info(sched)
except ValueError:
    logging.info('No schedules to append')
updSchedules = []
for monthSchedule in monthSchedules:
    if updSchedules.count(monthSchedule[1]['id'])==0:
        updSchedules.append(monthSchedule[1]['id'])
logging.info('----------Schedules in range [%s-%s] after purge----------' % (str(currentDtUtc), str(endDtUtc)))
for sched in updSchedules:
    logging.info(sched)
logging.info('----------Append schedules----------')
for updSchedule in updSchedules:
    schedule = allSchedules.find(updSchedule) #return last inserted so the oldest one
    logging.info(' -> base schedule %s' % str(schedule))
    if int(schedule[1]['repeat'])!=0:
        addSchedule(schedule[1], True, True)
logging.info('----------All schedules after append----------')
for sched in allSchedules:
    logging.info(sched[1])
"""
"""
logging.info('----------Purge schedules----------')
try:
    startDtUtc = nowUtc + relativedelta(months=-1)
    startTsUtc = int(startDtUtc.strftime('%s'))
    logging.info('now=%s start=%s' % (str(nowUtc), str(startDtUtc)))
    currentTsUtc = int(nowUtc.strftime('%s'))
    logging.info('now=%s start=%s' % (str(currentTsUtc), str(startTsUtc)))
    doneSchedules = timeSchedules.find_range(startTsUtc, currentTsUtc)
    logging.info(doneSchedules)
    for doneSchedule in doneSchedules:
        logging.info('->purge: %s' % str(doneSchedule))
    logging.info('Monthly purge removed %d schedules' % len(doneSchedules))
except:
    logging.exception('Monthly schedulings purge failed:')
"""
"""
quit('----------End of tests----------')
"""

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

