#!/usr/bin/env python

#stdlib imports
import urllib2
import urllib
import json
import os.path
from datetime import datetime,timedelta
import re
from xml.dom import minidom 
import sys
import shutil
from collections import OrderedDict
import calendar

#third-party imports
from neicmap import distance
import fixed
import numpy

#SERVER = 'dev-earthquake.cr' #comcat server name
SERVER = 'earthquake' #comcat server name
URLBASE = 'http://[SERVER].usgs.gov/fdsnws/event/1/query?%s'.replace('[SERVER]',SERVER)
COUNTBASE = 'http://[SERVER].usgs.gov/fdsnws/event/1/count?%s'.replace('[SERVER]',SERVER)
CHECKBASE = 'http://[SERVER].usgs.gov/fdsnws/event/1/%s'.replace('[SERVER]',SERVER)
EVENTURL = 'http://[SERVER].usgs.gov/fdsnws/event/1/query?eventid=[EVENTID]&format=geojson'.replace('[SERVER]',SERVER)
ALLPRODURL = 'http://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&includesuperseded=true&eventid=[EVENTID]'
#EVENTURL = 'http://[SERVER].cr.usgs.gov/fdsnws/event/1/query?eventid=[EVENTID]&format=geojson'.replace('[SERVER]',SERVER)
TIMEFMT = '%Y-%m-%dT%H:%M:%S'
NAN = float('nan')
KM2DEG = 1.0/111.191
MTYPES = ['usmww','usmwb','usmwc','usmwr','gcmtmwc','cimwr','ncmwr']

WEEKSECS = 86400*7

TIMEWINDOW = 16
DISTWINDOW = 100

def getUTCTimeStamp(timestamp):
    """Input is milliseconds, can be negative.
    Designed as a workaround for an apparent lack of Windows C time functions to handle negative values.
    """
    d = datetime(1970, 1, 1) + timedelta(microseconds=(timestamp*1000))
    return d

def getURLHandle(url):
    try:
        fh = urllib2.urlopen(url)
    except:
        try:
            req = urllib2.Request(url)
            req.add_unredirected_header('User-Agent', 'Custom User-Agent')
            fh = urllib2.urlopen(req)
        except:
            raise Exception('Could not open url "%s"' % url)
    return fh

def getAllVersions(eventid,productname,contentlist,folder=os.getcwd()):
    url = ALLPRODURL.replace('[EVENTID]',eventid)
    fh = getURLHandle(url)
    data = fh.read()
    fh.close()
    jdict = json.loads(data)
    if not jdict['properties']['products'].has_key(productname):
        raise Exception,"No %s product found for event %s" % (productname,eventid)
    products = jdict['properties']['products'][productname]
    outfiles = []
    if not os.path.isdir(folder):
        os.makedirs(folder)
    for product in products:
        print 'Looking at %s product with update time %i' % (productname,product['updateTime'])
        if product['code'] != eventid:
            continue
        pkeys = product['contents'].keys()
        if contentlist[0] not in pkeys:
            pass
        ptime = product['updateTime']
        for pkey in pkeys:
            path,contentfile = os.path.split(pkey)
            contentbase,contentext = os.path.splitext(contentfile)
            for content in contentlist:
                if contentfile.lower() == content.lower():
                    contenturl = product['contents'][pkey]['url']
                    fh = getURLHandle(contenturl)
                    data = fh.read()
                    outfile = os.path.join(folder,'%s_%s_%i%s' % (eventid,contentbase,ptime,contentext))
                    outfiles.append(outfile)
                    f = open(outfile,'wb')
                    f.write(data)
                    f.close()
                    fh.close()
                
    return outfiles

def getTimeSegments2(starttime,endtime):
    #startsecs = int(starttime.strftime('%s'))
    startsecs = calendar.timegm(starttime.timetuple())
    #endsecs = int(endtime.strftime('%s'))
    endsecs = calendar.timegm(endtime.timetuple())
    starts = range(startsecs,endsecs,WEEKSECS)
    ends = range(startsecs+WEEKSECS,endsecs+WEEKSECS,WEEKSECS)
    if ends[-1] > endsecs:
        ends[-1] = endsecs
    segments = []
    if len(starts) != len(ends):
        raise IndexError('Number of time segment starts/ends does not match for times: "%s" and "%s"' % (starttime,endtime))
    for start,end in zip(starts,ends):
        segments.append((datetime.utcfromtimestamp(start),datetime.utcfromtimestamp(end)))

    return segments

def getTimeSegments(segments,bounds,radius,starttime,endtime,magrange,catalog,contributor):
    """
    Return a list of datetime (start,end) tuples which will result in searches less than 20,000 events.
    @param segments: (Initially) empty list of (start,end) datetime tuples.
    @param bounds: Tuple of (lonmin,lonmax,latmin,latmax) spatial bounds or None.
    @param radius: Tuple of (lat,lon,minradiuskm,maxradiuskm) radius search parameters or None.
    @param starttime: Datetime of desired start time for search.
    @param endtime: Datetime of desired end time for search.
    @param magrange: Tuple of magnitude range (min,max).
    @param catalog: Specific catalog which matching events should have as a (not the only) source.
    @param contributor: Specific contributor which matching events should have as a (not the only) source.
    @return: List of datetime (start,end) tuples which will result in searches less than 20,000 events.
    """
    stime = starttime
    etime = endtime
    
    dt = etime - stime
    dtseconds = dt.days*86400 + dt.seconds
    #segment 1
    newstime = stime
    newetime = stime + timedelta(seconds=dtseconds/2)
    nevents,maxevents = getEventCount(bounds=bounds,radius=radius,starttime=newstime,endtime=newetime,
                                      magrange=magrange,catalog=catalog,contributor=contributor)
    if nevents < maxevents:
        segments.append((newstime,newetime))
    else:
        segments = getTimeSegments(segments,bounds,radius,newstime,newetime,
                                   magrange,catalog,contributor)
    #segment 2
    newstime = newetime
    newetime = etime
    nevents,maxevents = getEventCount(bounds=bounds,radius=radius,
                                      starttime=newstime,endtime=newetime,
                                      magrange=magrange,catalog=catalog,
                                      contributor=contributor)
    if nevents < maxevents:
        segments.append((newstime,newetime))
    else:
        segments = getTimeSegments(segments,bounds,radius,newstime,newetime,
                                   magrange,catalog,contributor)

    return segments

def __getEuclidean(lat1,lon1,time1,lat2,lon2,time2,dwindow=DISTWINDOW,twindow=TIMEWINDOW):
    dd = distance.sdist(lat1,lon1,lat2,lon2)/1000.0
    normd = dd/dwindow
    if time2 > time1:
        dt = time2-time1
    else:
        dt = time1-time2
    nsecs = dt.days*86400 + dt.seconds
    normt = nsecs/twindow
    euclid = numpy.sqrt(normd**2 + normt**2)
    return (euclid,dd,nsecs)

def associate(event,distancewindow=DISTWINDOW,timewindow=TIMEWINDOW,catalog=None):
    """
    Find possible matching events from ComCat for an input event.
    @param event: Dictionary containing fields ['lat','lon','time']
    @keyword distancewindow: Search distance in km.
    @keyword timewindow: Time search delta in seconds.
    @keyword catalog: Earthquake catalog to search.
    @return: List of origin dictionaries, with following keys:
             - time datetime of the origin
             - lat  Latitude of the origin
             - lon  Longitude of the origin
             - depth Depth of the origin
             - mag   Magnitude of the origin
             - id    ID of the authoritative origin.
             - euclidean Euclidean distance from the input event to this origin (dimensions are time in sec and dist in km)
             - timedelta Time delta between input event and this origin (seconds)
             - distance  Distance between input event and this origin (km)
    """
    lat = event['lat']
    lon = event['lon']
    etime = event['time']
    APITIMEFMT = '%Y-%m-%dT%H:%M:%S.%f'
    mintime = etime - timedelta(seconds=timewindow)
    maxtime = etime + timedelta(seconds=timewindow)

    eventlist = getEventData(radius=(lat,lon,0,distancewindow),starttime=mintime,endtime=maxtime,catalog=catalog)
    origins = []
    for e in eventlist:
        euclid,ddist,tdist = __getEuclidean(lat,lon,etime,e['lat'],e['lon'],e['time'],
                                                   dwindow=distancewindow,twindow=timewindow)
        e['euclidean'] = euclid
        e['timedelta'] = tdist
        e['distance'] = ddist
        origins.append(e.copy())

    origins = sorted(origins,key=lambda origin: origin['euclidean'])
    return origins

def parseEQXML(equrl):
    fh = getURLHandle(equrl)
    data = fh.read()
    fh.close()
    root = minidom.parseString(data)
    magel = root.getElementsByTagName('Event')[0].getElementsByTagName('Origin')[0].getElementsByTagName('Magnitude')[0]
    magval = float(magel.getElementsByTagName('Value')[0].firstChild.data)
    magtype = magel.getElementsByTagName('TypeKey')[0].firstChild.data
    magsrc = root.getElementsByTagName('Event')[0].getElementsByTagName('DataSource')[0].firstChild.data
    root.unlink()
    return ([magval],[magtype],[magsrc])

def parseQuakeML(quakeurl):
    mags = []
    magtypes = []
    magsources = []
    fh = getURLHandle(quakeurl)
    data = fh.read()
    fh.close()
    root = minidom.parseString(data)
    event = root.getElementsByTagName('event')[0]
    magels = event.getElementsByTagName('magnitude')
    for mag in magels:
        magval = float(mag.getElementsByTagName('mag')[0].getElementsByTagName('value')[0].firstChild.data)
        magtype = mag.getElementsByTagName('type')[0].firstChild.data
        try:
            magsrc = mag.getElementsByTagName('creationInfo')[0].getElementsByTagName('agencyID')[0].firstChild.data
        except:
            magsrc = 'NA'
        mags.append(magval)
        magtypes.append(magtype)
        magsources.append(magsrc)
    root.unlink()
    return (mags,magtypes,magsources) 

def __getAllMagnitudes(origins):
    mags = []
    magtypes = []
    magsources = []
    for origin in origins:
        isquakeml = origin['contents'].has_key('quakeml.xml')
        iseqxml = origin['contents'].has_key('eqxml.xml')
        if isquakeml:
            try:
                quakeurl = origin['contents']['quakeml.xml']['url']
                tmags,tmagtypes,tmagsources = parseQuakeML(quakeurl)
            except Exception,mobj:
                pass
        else:
            try:
                quakeurl = origin['contents']['eqxml.xml']['url']
                tmags,tmagtypes,tmagsources = parseEQXML(quakeurl)
            except Exception,mobj:
                pass
        mags += tmags
        magtypes += tmagtypes
        magsources += tmagsources
        
    return (mags,magtypes,magsources)

def __getMomentComponents(edict,momentType):
    mrr = float('nan')
    mtt = float('nan')
    mpp = float('nan')
    mrt = float('nan')
    mrp = float('nan')
    mtp = float('nan')
    momentlat = float('nan')
    momentlon = float('nan')
    momentdepth = float('nan')
    duration = float('nan')
    mtype = 'NA'
    tensor = None
    if momentType is None: #only check for matching moment tensor type if someone asked for it
        for i in range(0,len(edict['properties']['products']['moment-tensor'])):
            tensor = edict['properties']['products']['moment-tensor'][i]
            break
        if tensor is not None:
            try:
                mtype = __getMomentType(tensor)
            except:
                pass
    else:
        for tensor in edict['properties']['products']['moment-tensor']:
            mtype = __getMomentType(tensor)
            if mtype.lower() == momentType.lower():
                break
    if tensor is not None and tensor['properties'].has_key('tensor-mrr'):
        mrr = float(tensor['properties']['tensor-mrr'])
        mtt = float(tensor['properties']['tensor-mtt'])
        mpp = float(tensor['properties']['tensor-mpp'])
        mrt = float(tensor['properties']['tensor-mrt'])
        mrp = float(tensor['properties']['tensor-mrp'])
        mtp = float(tensor['properties']['tensor-mtp'])
        try:
            momentlat = float(tensor['properties']['derived-latitude'])
            momentlon = float(tensor['properties']['derived-longitude'])
        except:
            pass
        try:
            momentdepth = float(tensor['properties']['derived-depth'])
        except:
            pass
        try:
            duration = float(float(tensor['properties']['sourcetime-duration']))
        except:
            pass
                            
    return (mrr,mtt,mpp,mrt,mrp,mtp,mtype,momentlat,momentlon,momentdepth,duration)

def __getFocalAngles(edict):
    product = 'focal-mechanism'
    backup_product = None
    if 'moment-tensor' in edict['properties']['products'].keys():
        product = 'moment-tensor'
        if 'focal-mechanism' in edict['properties']['products'].keys():
            backup_product = 'focal-mechanism'
    strike1 = float('nan')
    dip1 = float('nan')
    rake1 = float('nan')
    strike2 = float('nan')
    dip2 = float('nan')
    rake2 = float('nan')
    if not edict['properties']['products'][product][0].has_key('properties'):
        if not edict['properties']['products'][product][0]['properties'].has_key('nodal-plane-1-dip'):
            if backup_product is not None and edict['properties']['products'][backup_product][0]['properties'].has_key('nodal-plane-1-dip'):
                strike1,dip1,rake1,strike2,dip2,rake2 = __getAngles(edict['properties']['products'][0][backup_product])
            else:
                return (strike1,dip1,rake1,strike2,dip2,rake2)

    strike1,dip1,rake1,strike2,dip2,rake2 = __getAngles(edict['properties']['products'][product][0])
    return (strike1,dip1,rake1,strike2,dip2,rake2)

def __getAngles(product):
    strike1 = float(product['properties']['nodal-plane-1-strike'])
    dip1 = float(product['properties']['nodal-plane-1-dip'])
    if product['properties'].has_key('nodal-plane-1-rake'):
        rake1 = float(product['properties']['nodal-plane-1-rake'])
    else:
        rake1 = float(product['properties']['nodal-plane-1-slip'])
    strike2 = float(product['properties']['nodal-plane-2-strike'])
    dip2 = float(product['properties']['nodal-plane-2-dip'])
    if product['properties'].has_key('nodal-plane-2-rake'):
        rake2 = float(product['properties']['nodal-plane-2-rake'])
    else:
        rake2 = float(product['properties']['nodal-plane-2-slip'])
    return (strike1,dip1,rake1,strike2,dip2,rake2)

def __getMomentType(tensor):
    mtype = 'NA'
    mtype1 = 'NA'
    mtype2 = 'NA'
    msource = 'NA'
    if tensor['properties'].has_key('beachball-source'):
        msource = tensor['properties']['beachball-source'].lower()
    if msource == 'pde' or msource == 'neic':
        msource = 'us'
    if msource == 'ld':
        msource = 'gcmt'
    if tensor['properties'].has_key('beachball-type'):
        mtype1 = msource+tensor['properties']['beachball-type']
    if tensor['properties'].has_key('derived-magnitude-type'):
        mtype2 = msource+tensor['properties']['derived-magnitude-type']
    if mtype1.lower() in MTYPES:
        mtype = mtype1
    else:
        if mtype2.lower() in MTYPES:
            mtype = mtype2
    return mtype
        

def checkCatalogs():
    """
    Return the list of valid ComCat catalogs.
    @return: List of valid ComCat catalog strings.
    """
    url = CHECKBASE % 'catalogs'
    catalogs = []
    try:
        fh = getURLHandle(url)
        #fh = urllib2.urlopen(url)
        data = fh.read()
        dom = minidom.parseString(data)
        fh.close()
        catalog_elements = dom.getElementsByTagName('Catalog')
        for catel in catalog_elements:
            if catel.firstChild is None:
                continue
            catalog = catel.firstChild.data.strip()
            if len(catalog):
                catalogs.append(str(catalog))
    except:
        raise Exception,"Could not open %s to search for list of catalogs" % url
    return catalogs    

def checkContributors():
    """
    Return the list of valid ComCat contributors.
    @return: List of valid ComCat contributor strings.
    """
    url = CHECKBASE % 'contributors'
    contributors = []
    try:
        fh = getURLHandle(url)
        #fh = urllib2.urlopen(url)
        data = fh.read()
        dom = minidom.parseString(data)
        fh.close()
        contributor_elements = dom.getElementsByTagName('Contributor')
        for catel in contributor_elements:
            if catel.firstChild is None:
                continue
            contributor = catel.firstChild.data.strip()
            if len(contributor):
                contributors.append(str(contributor))
    except:
        raise Exception,"Could not open %s to search for list of contributors" % url
    return contributors    

def getEventParams(bounds,radius,starttime,endtime,magrange,
                   catalog,contributor):
    urlparams = {}
    if starttime is not None:
        urlparams['starttime'] = starttime.strftime(TIMEFMT)
        if endtime is None:
            urlparams['endtime'] = datetime.utcnow().strftime(TIMEFMT)
    else:
        t30 = datetime.utcnow()-timedelta(days=30)
        urlparams['starttime'] = t30.strftime(TIMEFMT)
    if endtime is not None:
        #trap for when someone was lazy and entered the end-time in YYYY-MM-DD format
        #most likely they really want the END of the day, not the beginning.
        if endtime.hour == 0 and endtime.minute == 0 and endtime.second == 0:
            endtime = datetime(endtime.year,endtime.month,endtime.day,23,59,59)
        urlparams['endtime'] = endtime.strftime(TIMEFMT)
        if starttime is None:
            urlparams['starttime'] = datetime(1900,1,1,0,0,0).strftime(TIMEFMT)
    else:
        urlparams['endtime'] = datetime.utcnow().strftime(TIMEFMT)

    #we're using a rectangle search here
    if bounds is not None:
        urlparams['minlongitude'] = bounds[0]
        urlparams['maxlongitude'] = bounds[1]
        urlparams['minlatitude'] = bounds[2]
        urlparams['maxlatitude'] = bounds[3]

        #fix possible issues with 180 meridian crossings
        minwest = urlparams['minlongitude'] > 0 and urlparams['minlongitude'] < 180
        maxeast = urlparams['maxlongitude'] < 0 and urlparams['maxlongitude'] > -180
        if minwest and maxeast:
            urlparams['maxlongitude'] += 360

    if radius is not None:
        urlparams['latitude'] = radius[0]
        urlparams['longitude'] = radius[1]
        urlparams['minradiuskm'] = radius[2]
        urlparams['maxradiuskm'] = radius[3]
            
    if magrange is not None:
        urlparams['minmagnitude'] = magrange[0]
        urlparams['maxmagnitude'] = magrange[1]
    
    if catalog is not None:
        urlparams['catalog'] = catalog
    if contributor is not None:
        urlparams['contributor'] = contributor

    return urlparams

def getEventCount(bounds = None,radius=None,starttime = None,endtime = None,magrange = None,
                 catalog = None,contributor = None):
    if catalog is not None and catalog not in checkCatalogs():
        raise Exception,'Unknown catalog %s' % catalog
    if contributor is not None and contributor not in checkContributors():
        raise Exception,'Unknown contributor %s' % contributor

    #Make sure user is not specifying bounds search AND radius search
    if bounds is not None and radius is not None:
        raise Exception,'Cannot choose bounds search AND radius search.'

    urlparams = getEventParams(bounds,radius,starttime,endtime,magrange,
                               catalog,contributor)
    urlparams['format'] = 'geojson'
    params = urllib.urlencode(urlparams)
    url = COUNTBASE % params
    fh = getURLHandle(url)
    #fh = urllib2.urlopen(url)
    data = fh.read()
    fh.close()
    cdict = json.loads(data)
    nevents = cdict['count']
    maxevents = cdict['maxAllowed']
    return (nevents,maxevents)
    
    
def getEventData(bounds = None,radius=None,starttime = None,endtime = None,magrange = None,
                 catalog = None,contributor = None,getComponents=False,
                 getAngles=False,verbose=False,limitType=None,getAllMags=False):
    """Download a list of event dictionaries that could be represented in csv or tab separated format.

    The data will include, but not be limited to:
     - event id
     - date/time
     - lat
     - lon
     - depth
     - magnitude
     - event-type

    optionally, you can select to download (when available):
     - moment tensor components:
       - mrr
       - mtt
       - mpp
       - mtp
       - mrt
       - mrp
     - focal mechanism angles:
       - Nodal Plane 1 strike
       - Nodal Plane 1 dip
       - Nodal Plane 1 rake
     - Centroid lat,lon, depth, time
     - Magnitude type (Mwc, Mwb, Mww, etc.)
     - Duration
    @keyword bounds: (lonmin,lonmax,latmin,latmax) Bounding box of search. (dd)
    @keyword radius: (centerlat,centerlon,minradius,maxradius) Radius search parameters (dd,dd,km,km)
    @keyword starttime: Start time of search (datetime)
    @keyword endtime: End  time of search (datetime)
    @keyword magrange: (magmin,magmax) Magnitude range.
    @keyword catalog: Name of contributing catalog (see checkCatalogs()).
    @keyword contributor: Name of contributing catalog (see checkContributors()).
    @keyword getComponents: Boolean indicating whether to retrieve moment tensor components, type, and derived hypocenter (if available).
    @keyword getAngles: Boolean indicating whether to retrieve nodal plane angles (if available).
    @keyword verbose: Boolean indicating whether to print message to stderr for every event being retrieved. 
    @keyword limitType: Limit moment tensor retrieved to those of a particular source/type (comcat.MTYPES)
    """
    if catalog is not None and catalog not in checkCatalogs():
        raise Exception,'Unknown catalog %s' % catalog
    if contributor is not None and contributor not in checkContributors():
        raise Exception,'Unknown contributor %s' % contributor

    #Make sure user is not specifying bounds search AND radius search
    if bounds is not None and radius is not None:
        raise Exception,'Cannot choose bounds search AND radius search.'
    
    #start creating the url parameters
    urlparams = getEventParams(bounds,radius,starttime,endtime,magrange,
                               catalog,contributor)

    #search parameters we're not making available to the user (yet)
    urlparams['orderby'] = 'time-asc'
    urlparams['format'] = 'geojson'
    params = urllib.urlencode(urlparams)
    eventlist = []
    url = URLBASE % params
    fh = getURLHandle(url)
    #fh = urllib2.urlopen(url)
    feed_data = fh.read()
    fh.close()
    fdict = json.loads(feed_data)
    maxmags = 0
    for feature in fdict['features']:
        eventdict = OrderedDict()
        eventdict['id'] = [feature['id'],'%s']
        #eventdict['idlist'] = (feature['properties']['ids'].strip(',').split(','),'%s')
        if verbose:
            sys.stderr.write('Fetching data for event %s...\n' % eventdict['id'])
        eventdict['time'] = [getUTCTimeStamp(feature['properties']['time']),'%s']
        eventdict['lat'] = [feature['geometry']['coordinates'][1],'%.4f']
        eventdict['lon'] = [feature['geometry']['coordinates'][0],'%.4f']
        depth = feature['geometry']['coordinates'][2]
        mag = feature['properties']['mag']
        if mag is None:
            mag = float('nan')
        if depth is None:
            depth = float('nan')
        eventdict['depth'] = [depth,'%.1f']
        eventdict['mag'] = [mag,'%.1f']
        eventdict['event-type'] = [feature['properties']['type'],'%s']
                
        if not getComponents and not getAngles and not getAllMags:
            eventlist.append(eventdict.copy())
            continue
        eurl = feature['properties']['detail']
        #eventdict['url'] = [eurl,'%s']
        fh = getURLHandle(eurl)
        #fh = urllib2.urlopen(eurl)
        data = fh.read()
        fh.close()
        #sys.stderr.write('%s - After reading %s\n' % (datetime.now(),url))
        edict = json.loads(data)
        #sometimes you find when you actually open the json for the event that it doesn't
        #REALLY have a moment tensor or focal mechanism, just delete messages for some that USED to be
        #there.  Double-checking below.
        if edict['properties']['products'].has_key('moment-tensor'):
            hasMoment = edict['properties']['products']['moment-tensor'][0]['status'] != 'DELETE'
        else:
            hasMoment = False
        if edict['properties']['products'].has_key('focal-mechanism'):
            hasFocal = edict['properties']['products']['focal-mechanism'][0]['status'] != 'DELETE'
        else:
            hasFocal = False
        if getAllMags:
            if edict['properties']['products'].has_key('phase-data'):
                mags,magtypes,magsources = __getAllMagnitudes(edict['properties']['products']['phase-data'])
            else:
                mags,magtypes,magsources = __getAllMagnitudes(edict['properties']['products']['origin'])
            i = 1
            if len(mags) > maxmags:
                maxmags = len(mags)
            for mag,magtype,magsource in zip(mags,magtypes,magsources):
                eventdict['mag%i' % i] = [mag,'%.1f']
                eventdict['mag%i-source' % i] = [magsource,'%s']
                eventdict['mag%i-type' % i] = [magtype,'%s']
                #sys.stderr.write('Getting mag %i from event %s\n' % (i,feature['id']))
                i += 1
        if getComponents:
            if hasMoment:
                mrr,mtt,mpp,mrt,mrp,mtp,mtype,mlat,mlon,mdepth,mduration = __getMomentComponents(edict,limitType)
                eventdict['mrr'] = [mrr,'%g']
                eventdict['mtt'] = [mtt,'%g']
                eventdict['mpp'] = [mpp,'%g']
                eventdict['mrt'] = [mrt,'%g']
                eventdict['mrp'] = [mrp,'%g']
                eventdict['mtp'] = [mtp,'%g']
                eventdict['type'] = [mtype,'%s']
                eventdict['moment-lat'] = [mlat,'%.4f']
                eventdict['moment-lon'] = [mlon,'%.4f']
                eventdict['moment-depth'] = [mdepth,'%.1f']
                eventdict['moment-duration'] = [mduration,'%.1f']
            else:
                eventdict['mrr'] = [NAN,'%g']
                eventdict['mtt'] = [NAN,'%g']
                eventdict['mpp'] = [NAN,'%g']
                eventdict['mrt'] = [NAN,'%g']
                eventdict['mrp'] = [NAN,'%g']
                eventdict['mtp'] = [NAN,'%g']
                eventdict['type'] = ['NA','%s']
                eventdict['moment-lat'] = [NAN,'%.4f']
                eventdict['moment-lon'] = [NAN,'%.4f']
                eventdict['moment-depth'] = [NAN,'%.1f']
                eventdict['moment-duration'] = [NAN,'%.1f']
        if getAngles:
            #sometimes there are delete products instead of real ones, fooling you into
            #thinking that there is really a moment tensor.  Trapping for that here.
            if hasFocal or hasMoment:
                strike1,dip1,rake1,strike2,dip2,rake2 = __getFocalAngles(edict)
                eventdict['strike1'] = [strike1,'%.0f']
                eventdict['dip1'] = [dip1,'%.0f']
                eventdict['rake1'] = [rake1,'%.0f']
                eventdict['strike2'] = [strike2,'%.0f']
                eventdict['dip2'] = [dip2,'%.0f']
                eventdict['rake2'] = [rake2,'%.0f']
            else:
                eventdict['strike1'] = [NAN,'%.0f']
                eventdict['dip1'] = [NAN,'%.0f']
                eventdict['rake1'] = [NAN,'%.0f']
                eventdict['strike2'] = [NAN,'%.0f']
                eventdict['dip2'] = [NAN,'%.0f']
                eventdict['rake2'] = [NAN,'%.0f']
        eventlist.append(eventdict.copy())
    return (eventlist,maxmags)

def getPhaseData(bounds = None,radius=None,starttime = None,endtime = None,
                 magrange = None,catalog = None,contributor = None,
                 eventid = None,eventProperties=None,productProperties=None,verbose=False):
    """Fetch origin, moment tensor and phase data for earthquakes matching input parameters.

    @keyword bounds: Sequence of (lonmin,lonmax,latmin,latmax)
    @keyword radius: Sequence of (lat,lon,radiusmin [km],radiusmax [km]).
    @keyword starttime: Start time for search (defaults to ~30 days ago). YYYY-mm-ddTHH:MM:SS
    @keyword endtime: End time for search (defaults to now). YYYY-mm-ddTHH:MM:SS
    @keyword magrange: Sequence of (minmag,maxmag)
    @keyword catalog: Product catalog to use to constrain the search (centennial,nc, etc.).
    @keyword contributor: Product contributor, or who sent the product to ComCat (us,nc,etc.).
    @keyword eventid: Event id to search for - restricts search to a single event (usb000ifva)
    @keyword eventProperties: Dictionary of event properties to match. {'reviewstatus':'approved'}
    @keyword productProperties: Dictionary of event properties to match. {'alert':'yellow'}
    @return: List of dictionaries, where the fields are:
             - eventcode (usually) 10 character event code
             - magerr Magnitude uncertainty
             - origins List of origin dictionaries, with fields:
               - time Datetime object
               - year, month, day, hour, minute and (fractional) second
               - timefixed Flag indicating whether time was fixed for inversion.
               - time_error (seconds)
               - timerms Root mean square of time residuals
               - lat, lon Position (degrees)
               - epifixed Flag indicating whether epicenter was fixed for inversion.
               - semimajor Semi-major axis of error ellipse
               - semiminor Semi-minor axis of error ellipse
               - errorazimuth Azimuth of error ellipse
               - depth (km)
               - depthfixed Flag indicating whether depth was fixed for inversion.
               - deptherr (km)
               - numphases Number of defining phases
               - numstations Number of defining stations
               - azgap Gap in azimuthal coverage (degrees)
               - mindist Distance to closest station (degrees)
               - maxdist Distance to furthest station (degrees)
               - analysistype (a=automatic, m=manual)
               - locmethod (i=inversion)
               - event_type (ke = known earthquake, se= suspected earthquake)
               - author Author of the origin
               - originID ID of the origin
             -phases List of phase dictionaries, with fields:
               - stationcode Station code
               - stationdist Event to station distance (degrees)
               - stationaz Event to station azimuth (degrees)
               - phasecode Phase code
               - time Phase arrival time (datetime)
               - hour, minute, (fractional) second Phase arrival time
               - timeres Time residual (seconds)
               - azimuth Observed azimuth (degrees)
               - azres Azimuth residual (degrees)
               - slowness Observed slowness
               - slowres Slowness residuals
               - timeflag Time defining flag
               - azflag Azimuth defining flag
               - slowflag Slowness defining flag
               - snr Signal to noise ratio
               - amplitude Amplitude (nanometers)
               - period (seconds)
               - picktype (a=automatic,m=manual)
               - direction Direction of short period motion
               - quality Onset quality
               - magtype (mb, ms, etc.)
               - minmax Min max indicator
               - mag Magnitude value
               - arrid Arrival ID
             -tensors List of moment tensor dictionaries, with fields:
               - m0 Scalar moment (no exponent)
               - exponent Exponent of the moment tensor and MXX fields.
               - scalarmoment Scalar moment, divided by 10^exponent
               - fclvd Fraction of moment released as a compensated linear vector dipole
               - mrr radial-radial element of moment tensor
               - mtt theta-theta element of moment tensor
               - mpp phi-phi element of moment tensor
               - mrt radial-theta element of moment tensor
               - mtp theta-phi element of moment tensor
               - phi-radial element of moment tensor
               - nbodystations Number of body wave stations used
               - nsurfacestations Number of surface wave stations used
               - author Author of the moment tensor
               - momenterror Error in scalar moment
               - clvderror Error in clvd
               - errormrr, errormtt, errormpp, errormrt,errormrp,errormtp Errors in elements
               - nbody Number of body wave components used
               - nsurface Number of surface wave components used
               - duration Source duration (seconds)
    """

    #Make sure user is not specifying bounds search AND radius search
    if bounds is not None and radius is not None:
        raise Exception,'Cannot choose bounds search AND radius search.'
    
    if catalog is not None and catalog not in checkCatalogs():
        raise Exception,'Unknown catalog %s' % catalog
    if contributor is not None and contributor not in checkContributors():
        raise Exception,'Unknown contributor %s' % contributor
    
    #if someone asks for a specific eventid, then we can shortcut all of this stuff
    #below, and just parse the event json
    if eventid is not None:
        try:
            phaseml = __getEventPhase(eventid)
            return [phaseml]
        except Exception,msg:
            sys.stderr.write('Could not retrieve phase data for eventid "%s" - error "%s"\n' % (eventid,str(msg)))
            return None

    #start creating the url parameters
    urlparams = {}
    urlparams['producttype'] = 'phase-data'
    if starttime is not None:
        urlparams['starttime'] = starttime.strftime(TIMEFMT)
        if endtime is None:
            urlparams['endtime'] = datetime.utcnow().strftime(TIMEFMT)
    if endtime is not None:
        urlparams['endtime'] = endtime.strftime(TIMEFMT)
        if starttime is None:
            urlparams['starttime'] = datetime(1900,1,1,0,0,0).strftime(TIMEFMT)

    #we're using a rectangle search here
    if bounds is not None:
        urlparams['minlongitude'] = bounds[0]
        urlparams['maxlongitude'] = bounds[1]
        urlparams['minlatitude'] = bounds[2]
        urlparams['maxlatitude'] = bounds[3]

        #fix possible issues with 180 meridian crossings
        minwest = urlparams['minlongitude'] > 0 and urlparams['minlongitude'] < 180
        maxeast = urlparams['maxlongitude'] < 0 and urlparams['maxlongitude'] > -180
        if minwest and maxeast:
            urlparams['maxlongitude'] += 360

    if radius is not None:
        urlparams['latitude'] = radius[0]
        urlparams['longitude'] = radius[1]
        urlparams['minradiuskm'] = radius[2]
        urlparams['maxradiuskm'] = radius[3]

    if magrange is not None:
        urlparams['minmagnitude'] = magrange[0]
        urlparams['maxmagnitude'] = magrange[1]
    
    if catalog is not None:
        urlparams['catalog'] = catalog
    if contributor is not None:
        urlparams['contributor'] = contributor

    #search parameters we're not making available to the user (yet)
    urlparams['orderby'] = 'time-asc'
    urlparams['format'] = 'geojson'
    params = urllib.urlencode(urlparams)
    url = URLBASE % params
    fh = getURLHandle(url)
    #fh = urllib2.urlopen(url)
    feed_data = fh.read()
    fh.close()

    fdict = json.loads(feed_data)
    outfiles = []
    eqlist = []
    ic = 0
    for feature in fdict['features']:
        eid = feature['id']
        #REMOVE
        sys.stderr.write('Fetching event %s (%i of %i)\n' % (eid,ic+1,len(fdict['features'])))
        location = feature['properties']['place']
        ptypes = feature['properties']['types'].strip(',').split(',')
        if 'phase-data' not in ptypes:
            continue
        try:
            phaseml = __getEventPhase(eid)
            eqlist.append(phaseml)
        except Exception,msg:
            if verbose:
                sys.stderr.write('Could not retrieve data for eventid "%s" - error "%s"\n' % (eid,str(msg)))
        ic += 1
    return eqlist

def __getEventPhase(eventid):
    url = EVENTURL.replace('[EVENTID]',eventid)
    try:
        fh = getURLHandle(url)
        event_data = fh.read()
        fh.close()
        edict = json.loads(event_data)
        if not edict['properties']['products']['phase-data'][0]['contents'].has_key('quakeml.xml'):
            raise LookupError,'Event %s does not have a phase data quakeml file' % eventid
        quakeurl = edict['properties']['products']['phase-data'][0]['contents']['quakeml.xml']['url']
        fh = getURLHandle(quakeurl)
        quakedata = fh.read()
        fh.close()
        try:
            phaseml = fixed.PhaseML()
            phaseml.readFromString(quakedata,url=quakeurl)
        except Exception,ex:
            raise Exception('Could not parse phase data for event %s - error "%s"\n' % (eventid,str(ex)))
    except Exception,msg:
        raise Exception('Could not parse phase data for event %s - error "%s"\n' % (eventid,str(msg)))
    return phaseml    

def getContents(product,contentlist,outfolder=None,bounds = None,
                starttime = None,endtime = None,magrange = None,
                catalog = None,contributor = None,eventid = None,
                eventProperties=None,productProperties=None,radius=None,
                listURL=False,since=None,getAll=False):
    """
    Download product contents for event(s) from ComCat, given a product type and list of content files for that product.

    The possible product types include, but are not limited to:
     - origin
     - focal-mechanism
     - moment-tensor
     - shakemap
     - dyfi
     - losspager

    The possible list of contents is long, suffice it to say that you can figure out the name of the 
    content you want by exploring the "Downloads" tab of an event page.  For example, if you specify 
    "shakemap" in the "Search Downloads" box, you should see a long list of possible downloads.  Mouse \
    over the link for the product(s) of interest and note the file name at the end of the url.  Examples
    for ShakeMap include: "stationlist.txt", "stationlist.xml", "grid.xml".

    @param product: Name of desired product (i.e., shakemap).
    @param contentlist: List of desired contents.
    @keyword outfolder: Local directory where output files should be written (defaults to current working directory).
    @keyword bounds: Sequence of (lonmin,lonmax,latmin,latmax)
    @keyword starttime: Start time for search (defaults to ~30 days ago). YYYY-mm-ddTHH:MM:SS
    @keyword endtime: End time for search (defaults to now). YYYY-mm-ddTHH:MM:SS
    @keyword magrange: Sequence of (minmag,maxmag)
    @keyword catalog: Product catalog to use to constrain the search (centennial,nc, etc.).
    @keyword contributor: Product contributor, or who sent the product to ComCat (us,nc,etc.).
    @keyword eventid: Event id to search for - restricts search to a single event (usb000ifva)
    @keyword eventProperties: Dictionary of event properties to match. {'reviewstatus':'approved'}
    @keyword productProperties: Dictionary of event properties to match. {'alert':'yellow'}
    @keyword radius: Sequence of (lat,lon,minradius,maxradius)
    @keyword listURL: Boolean indicating whether URL for each product source should be printed to stdout.
    @keyword since: Limit to events after the specified time (datetime). 
    @keyword getAll: Get all versions of a product (only works when eventid keyword is set).
    @return: List of output files.
    @raise Exception: When:
      - Input catalog is invalid.
      - Input contributor is invalid.
      - Eventid was supplied, but not found in ComCat.
    """
    
    if catalog is not None and catalog not in checkCatalogs():
        raise Exception,'Unknown catalog %s' % catalog
    if contributor is not None and contributor not in checkContributors():
        raise Exception,'Unknown contributor %s' % contributor

    if outfolder is None:
        outfolder = os.getcwd()

    #make the output folder if it doesn't already exist
    if not os.path.isdir(outfolder):
        os.makedirs(outfolder)
    
    #if someone asks for a specific eventid, then we can shortcut all of this stuff
    #below, and just parse the event json
    if eventid is not None:
        try:
            outfiles = readEventURL(product,contentlist,outfolder,eventid,listURL=listURL,getAll=getAll)
            return outfiles
        except Exception,errobj:
            raise Exception,'Could not retrieve data for eventid "%s" due to "%s"' % (eventid,str(errobj))
    
    #start creating the url parameters
    urlparams = {}
    urlparams['producttype'] = product
    if starttime is not None:
        urlparams['starttime'] = starttime.strftime(TIMEFMT)
        if endtime is None:
            urlparams['endtime'] = datetime.utcnow().strftime(TIMEFMT)
    if endtime is not None:
        urlparams['endtime'] = endtime.strftime(TIMEFMT)
        if starttime is None:
            urlparams['starttime'] = datetime(1900,1,1,0,0,0).strftime(TIMEFMT)

    #if specified, only get events updated after a particular time
    if since is not None:
        urlparams['updatedafter'] = since.strftime(TIMEFMT)

    if bounds is not None and radius is not None:
        raise Exception,"Choose one of bounds or radius, not both"
        
    #we're using a rectangle search here
    if bounds is not None:
        urlparams['minlongitude'] = bounds[0]
        urlparams['maxlongitude'] = bounds[1]
        urlparams['minlatitude'] = bounds[2]
        urlparams['maxlatitude'] = bounds[3]

        #fix possible issues with 180 meridian crossings
        minwest = urlparams['minlongitude'] > 0 and urlparams['minlongitude'] < 180
        maxeast = urlparams['maxlongitude'] < 0 and urlparams['maxlongitude'] > -180
        if minwest and maxeast:
            urlparams['maxlongitude'] += 360

    if radius is not None:
        urlparams['latitude'] = radius[0]
        urlparams['longitude'] = radius[1]
        urlparams['minradiuskm'] = radius[2]
        urlparams['maxradiuskm'] = radius[3]

    if magrange is not None:
        urlparams['minmagnitude'] = magrange[0]
        urlparams['maxmagnitude'] = magrange[1]
    
    if catalog is not None:
        urlparams['catalog'] = catalog
    if contributor is not None:
        urlparams['contributor'] = contributor

    #search parameters we're not making available to the user (yet)
    urlparams['orderby'] = 'time-asc'
    urlparams['format'] = 'geojson'
    params = urllib.urlencode(urlparams)
    url = URLBASE % params
    #fh = urllib2.urlopen(url)
    fh = getURLHandle(url)
    feed_data = fh.read()
    fh.close()
    fdict = json.loads(feed_data)
    outfiles = []
    for feature in fdict['features']:
        if eventProperties is not None:
            skip=False
            for key,value in eventProperties.iteritems():
                if not feature['properties'].has_key(key):
                    skip=True
                    break
                else:
                    fvalue = feature['properties'][key]
                    if fvalue is None:
                        skip=True
                        break
                    if fvalue.lower() != value.lower():
                        skip=True
                        break
            if skip:
                continue
        eid = feature['id']
        lat,lon,depth = feature['geometry']['coordinates']
        mag = feature['properties']['mag']
        efiles = readEventURL(product,contentlist,outfolder,eid,listURL=listURL,productProperties=productProperties)
        outfiles += efiles

    return outfiles

def readEventURL(product,contentlist,outfolder,eid,listURL=False,productProperties=None,getAll=False):
    """
    Download contents for a given event.

    @param product: Name of desired product (i.e., shakemap).
    @param contentlist: List of desired contents.
    @param outfolder: Local directory where output files should be written (defaults to current working directory).
    @param eid: Event ID to search for.
    @param listURL: Boolean indicating whether URL for each product source should be printed to stdout.
    @param productProperties: Dictionary of event properties to match. {'alert':'yellow'}
    @returns: List of downloaded files.
    @raise Exception: When eventid URL could not be parsed.
    """
    if getAll:
        return getAllVersions(eid,product,contentlist,folder=outfolder)
    outfiles = []
    furl = EVENTURL.replace('[EVENTID]',eid)
    try:
        fh = getURLHandle(furl)
        #fh = urllib2.urlopen(furl)
        event_data = fh.read()
        fh.close()
        edict = json.loads(event_data)
        pdict = edict['properties']['products'][product][0]

        skip = False
        if productProperties is not None:
            for key,value in productProperties.iteritems():
                if pdict['properties'].has_key(key) and pdict['properties'][key] is not None:
                    if value.lower() != pdict['properties'][key].lower():
                        skip=True
                        break
                
        if skip:
            return outfiles
        if pdict['status'].lower() == 'delete':
            return []
        for content in contentlist:
            for contentkey in pdict['contents'].keys():
                path,contentfile = os.path.split(contentkey)
                if contentfile.lower() == content.lower():
                    contenturl = pdict['contents'][contentkey]['url']
                    if listURL:
                        print contenturl
                        continue
                    fh = getURLHandle(contenturl)
                    #fh = urllib2.urlopen(contenturl)
                    #print 'Downloading %s...' % contenturl
                    data = fh.read()
                    fh.close()
                    outfile = os.path.join(outfolder,'%s_%s' % (eid,contentfile))
                    f = open(outfile,'w')
                    f.write(data)
                    f.close()
                    outfiles.append(outfile)
    except Exception,msg:
        raise Exception,'Could not parse event information from "%s". Error: "%s"' % (furl,str(msg))
    return outfiles

if __name__ == '__main__':
    #test associate functionality
    event = {'lat':40.828,'lon':-125.135,'time':datetime(2014,3,10,5,18,15)}
    origins = associate(event)
    for origin in origins:
        print origin

    sys.exit(0)
    #test catalog/contributor checkers
    catalogs = checkCatalogs()
    print 'Catalogs are:'
    print catalogs
    print
    print 'Contributors are:'
    contributors = checkContributors()
    print contributors
    print

    #Downloads all of the shakemap stationlist.txt files for this California bounding box
    #within the last year
    #california bbox
    xmin = -125.15625
    xmax = -113.774414
    ymin = 32.600048
    ymax = 41.851151
    maxtime = datetime.utcnow()
    mintime = maxtime - timedelta(days=60)
    bounds = (xmin,xmax,ymin,ymax)
    outfolder = os.path.join(os.path.expanduser('~'),'tmpcomcatdata')
    outlist = getContents('shakemap',['stationlist.txt'],
                          outfolder = outfolder,
                          bounds=bounds,starttime=mintime,endtime=maxtime)
    print 'Downloaded %i files to %s.  Now deleting those files and the folder.' % (len(outlist),outfolder)
    shutil.rmtree(outfolder)

    #Get the shakemap grid from just a single event - let's choose Northridge
    eventid = 'pde19940117123055390_18'
    outlist = getContents('shakemap',['grid.xml'],
                          outfolder = outfolder,eventid=eventid)
    print 'I downloaded:'
    print outlist
    print 'Now cleaning up...'
    shutil.rmtree(outfolder)
    print 'Done.'
    
