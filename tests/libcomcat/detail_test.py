#!/usr/bin/env python

import os.path
import sys
from datetime import datetime,timedelta

# hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
pathdir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, pathdir)  # put this at the front of the system path,
# ignoring any other installations of this library

from libcomcat.detail import DetailEvent,search


def test():
    eventid = 'ci3144585' # northridge
    detail = DetailEvent(eventid)
    assert detail.id == 'ci3144585'
    assert detail.time == datetime(2018,1,25,6,15,0,535000)
    assert detail.latitude == 34.213
    assert detail.longitude == -118.537
    assert detail.depth == 18.202
    assert detail.magnitude == 6.7

    shakemap = detail.getProduct('shakemap')
    assert shakemap.hasContent('grid.xml')
    outfile = os.path.join(os.path.expanduser('~'),'%s_grid.xml' % detail.id)
    shakemap.getContent('grid.xml',outfile)

    assert shakemap.hasProperty('depth')
    assert shakemap['depth'] == '19'

    start_time = datetime(1994,1,17)
    end_time = datetime(1994,1,18)
    events = search(starttime=start_time,
                    endtime=end_time,minmagnitude=6.5)
    assert events[0].id == 'ci3144585'

    devent = events[0].getDetailEvent()
    assert devent.magnitude == 6.7
    edict = devent.toDict(get_all_magnitudes=True,get_all_tensors=True)
    x = 1
    
if __name__ == '__main__':
    test()
