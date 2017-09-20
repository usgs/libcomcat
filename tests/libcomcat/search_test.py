#!/usr/bin/env python

import os.path
import sys
from datetime import datetime,timedelta
import tempfile
import json

from libcomcat.search import search,count,get_event_by_id
from libcomcat.classes import DetailEvent

def test_get_event():
    eventid = 'ci3144585'
    event = get_event_by_id(eventid)
    assert isinstance(event,DetailEvent)

def test_count():
    nevents = count(starttime=datetime(1994,1,17,12,30),
                    endtime=datetime(1994,1,18,12,35),
                    minmagnitude=6.6,verbose=True,
                    updatedafter=datetime(2010,1,1))
    assert nevents == 1

def test_search():
    eventlist = search(starttime=datetime(1994,1,17,12,30),
                       endtime=datetime(1994,1,18,12,35),
                       minmagnitude=6.6)
    event = eventlist[0]
    assert event.id == 'ci3144585'

    events = search(minmagnitude=9.0,maxmagnitude=9.9,
                    updatedafter=datetime(2010,1,1))

    events = search(maxmagnitude=0.1,
                    starttime=datetime(2017,1,1),
                    endtime=datetime(2017,1,30))
    
if __name__ == '__main__':
    test_get_event()
    test_count()
    test_search()
    
