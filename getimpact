#!/usr/bin/env python

import urllib2
import json
import sys
from datetime import datetime
import argparse

if __name__ == '__main__':
    usage = '''
    Return the eventid,origin time,lat,lon,depth,magnitude,impact text for a given input event ID.

    If no impact-text product is found, then the text returned will be an empty string "".
    
    %(prog)s eventid

    Example:
    %(prog)s us10003vki
    
    Returns:
    us10003vki,2015-11-07 17:37:49,8.5000,-71.5000,5.0,4.9,"Felt (V) at Ejido."
    '''
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument('eventID', help='Event ID (i.e., us10003vki).')
    args = parser.parse_args()
    
    eventid = args.eventID
    url = 'http://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/%s.geojson' % eventid
    fh = urllib2.urlopen(url)
    data = fh.read()
    fh.close()
    jdict = json.loads(data)
    #get time,hypo, mag, and any impact-text product
    lon,lat,depth = jdict['geometry']['coordinates']
    etime = datetime.utcfromtimestamp(int(jdict['properties']['time']/1000))
    etimestr = etime.strftime('%Y-%m-%d %H:%M:%S')
    mag = jdict['properties']['mag']
    plist = jdict['properties']['products'].keys()
    if 'impact-text' in plist:
        itext = jdict['properties']['products']['impact-text'][0]['contents']['']['bytes'].strip()
    else:
        itext = ''

    print '%s,%s,%.4f,%.4f,%.1f,%.1f,"%s"' % (eventid,etimestr,lat,lon,depth,mag,itext)
    
