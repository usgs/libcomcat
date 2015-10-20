#!/usr/bin/env python

#stdlib imports
from xml.dom.minidom import parseString
import sys
import datetime
import math
import urllib2
import copy

#third party imports
import numpy as np
from neicio import fixed

#local imports
import ellipse

ORIGINHDR = [((4,7),'a4'),
             ((15,18),'a4'),
             ((27,29),'a3'),
             ((33,35),'a3'),
             ((37,44),'a8'),
             ((46,54),'a9'),
             ((57,60),'a4'),
             ((63,66),'a4'),
             ((69,70),'a2'),
             ((72,76),'a5'),
             ((80,82),'a3'),
             ((84,87),'a4'),
             ((89,92),'a4'),
             ((94,96),'a3'),
             ((99,103),'a5'),
             ((106,110),'a5'),
             ((112,115),'a4'),
             ((119,124),'a6'),
             ((131,136),'a6')]

#optional third element boolean indicates zero-padding (dates, usually)
ORIGINFMT = [((1,4),'i4',True), #year
          ((5,5),'a1'),
          ((6,7),'i2',True), #month
          ((8,8),'a1'),
          ((9,10),'i2',True), #day
          ((12,13),'i2',True), #hour
          ((14,14),'a1'),
          ((15,16),'i2',True), #minute
          ((17,17),'a1'),
          ((18,22),'f5.2',True), #second
          ((23,23),'a1'), #time fixed flag
          ((25,29),'f5.2'), #time error
          ((31,35),'f5.2'), #rms time residuals
          ((37,44),'f8.4'), #latitude
          ((46,54),'f9.4'), #longitude
          ((55,55),'a1'), #epicenter fixed flag
          ((56,60),'f5.1'), #semi major of error ellipse
          ((62,66),'f5.1'), #semi minor of error ellipse
          ((68,70),'i3'), #azimuth of error ellipse
          ((72,76),'f5.1'), #depth
          ((77,77),'a1'), #depth fixed flag
          ((79,82),'f4.1'), #depth error 90%
          ((84,87),'i4'), #number of phases
          ((89,92),'i4'), #number of stations
          ((94,96),'i3'), #gap in azimuth coverage
          ((98,103),'f6.2'), #distance to closest station (degrees)
          ((105,110),'f6.2'), #distance to furthest station
          ((112,112),'a1'), #analysis type: (a = automatic, m = manual, g = guess)
          ((114,114),'a1'), #location method: (i = inversion, p = pattern recognition, g = ground truth, o = other)
          ((116,117),'a2'), #event type: 
          ((119,127),'a9',False,True), #author
          ((129,136),'a8')] #origin id

MAGHDR = [((1,9),'a9'),
          ((12,14),'a3'),
          ((16,19),'a4'),
          ((21,26),'a6'),
          ((33,38),'a6')]

MAGFMT = [((1,5),'a5',False,True), #mag type
          ((6,6),'a1'), #min max indicator
          ((7,10),'f4.1'), #magnitude value
          ((12,14),'f3.1'), #magnitude error
          ((16,19),'i4'), #number of stations used
          ((21,29),'a9',False,True), #author
          ((31,38),'a8')] #origin id
           

PHASEHDR = [((1,3),'a3'),
            ((9,12),'a4'),
            ((15,18),'a4'),
            ((20,24),'a5'),
            ((33,36),'a4'),
            ((43,46),'a4'),
            ((49,52),'a4'),
            ((54,58),'a5'),
            ((62,65),'a4'),
            ((69,72),'a4'),
            ((74,76),'a3'),
            ((80,82),'a3'),
            ((90,92),'a3'),
            ((96,98),'a3'),
            ((100,103),'a4'),
            ((105,113),'a9'),
            ((118,122),'a5')]

#sprintf(m_szEntry, "\nSta     Dist  EvAz Phase        Time      Tres  Azim AzRes   Slow   SRes Def   SNR       Amp   Per Qual Magnitude    ArrID    Agy   Deploy   Ln Auth  Rep   PCh ACh L\n");

PHASELBL = ['Sta','Dist','EvAz','Phase','Time','TRes','Azim','AzRes','Slow',
            'SRes','Def','SNR','Amp','Per','Qual','Magnitude','ArrID']

PHASEFMT = [((1,5),'a5',False,True), #station code
            ((7,12),'f6.2'), #station distance
            ((14,18),'f5.1'), #station azimuth
            ((20,27),'a8',False,True), #phase code
            ((29,30),'i2',True), #hour
            ((31,31),'a1'),
            ((32,33),'i2',True), #minute
            ((34,34),'a1'),
            ((35,40),'f6.3',True), #second
            ((42,46),'f5.1'),
            ((48,52),'f5.1'),
            ((54,58),'f5.1'),
            ((60,64),'f5.1'),
            ((67,71),'f5.1'),
            ((74,74),'a1'),
            ((75,75),'a1'),
            ((76,76),'a1'),
            ((78,82),'f5.1'),
            ((84,92),'f9.1'),
            ((94,98),'f5.2'),
            ((100,100),'a1'),
            ((101,101),'a1'),
            ((102,102),'a1'),
            ((104,108),'a5'),
            ((109,109),'a1'),
            ((110,113),'f4.1'),
            ((115,122),'a8')]

MOMENTHDR1 = [((2,2),'a1'), #(
              ((3,10),'a8'), #MOMTENS
              ((12,13),'a2'), #sc
              ((18,19),'a2'), #M0
              ((21,25),'a5'), #fCLVD
              ((30,32),'a3'), #MRR
              ((37,39),'a3'), #MTT
              ((44,46),'a3'), #MPP
              ((51,53),'a3'), #MRT
              ((58,60),'a3'), #MTP
              ((65,67),'a3'), #MPR
              ((69,72),'a4'), #NST1
              ((74,77),'a4'), #NST2
              ((79,84),'a6')] #Author

MOMENTLBL1 = ['(','#MOMTENS','sc','M0','fCLVD','MRR','MTT','MPP',
              'MRT','MTP','MPR','NST1','NST2','Author']

MOMENTHDR2 = [((2,2),'a1'),
              ((3,3),'a1'),
              ((17,19),'a3'),
              ((21,25),'a5'),
              ((30,32),'a3'),
              ((37,39),'a3'),
              ((44,46),'a3'),
              ((51,53),'a3'),
              ((58,60),'a3'),
              ((65,67),'a3'),
              ((69,72),'a4'),
              ((74,77),'a4'),
              ((79,86),'a8')]

MOMENTLBL2 = ['(','#','eM0','eCLVD','eRR','eTT','ePP',
              'eRT','eTP','ePR','NCO1','NCO2','Duration']

MOMENTFMT1 = [((2,2),'a1'),
              ((3,3),'a1'),
              ((12,13),'i2'),
              ((15,19),'f5.3'),
              ((21,25),'f5.3'),
              ((27,32),'f6.3'),
              ((34,39),'f6.3'),
              ((41,46),'f6.3'),
              ((48,53),'f6.3'),
              ((55,60),'f6.3'),
              ((62,67),'f6.3'),
              ((69,72),'i4'),
              ((74,77),'i4'),
              ((79,87),'a9',False,True)]

MOMENTFMT2 = [((2,2),'a1'),
              ((3,3),'a1'),
              ((15,19),'f5.3'),
              ((21,25),'f5.3'),
              ((27,32),'f6.3'),
              ((34,39),'f6.3'),
              ((41,46),'f6.3'),
              ((48,53),'f6.3'),
              ((55,60),'f6.3'),
              ((62,67),'f6.3'),
              ((69,72),'i4'),
              ((74,77),'i4'),
              ((79,86),'f8.2')]

#ftp://hazards.cr.usgs.gov/weekly/ehdf.txt
EHDRFMT = [((1,2),'a2'), #GS
           ((3,4),'a2'), #blank
           ((5,8),'i4'), #year
           ((9,10),'i2',True), #month
           ((11,12),'i2',True), #day
           ((13,14),'i2',True), #hour
           ((15,16),'i2',True), #minute
           ((17,18),'i2',True), #second
           ((19,20),'i2',True), #hundredths of a second (??)
           ((21,25),'i5'), #lat
           ((26,26),'a1'), #N or S
           ((27,32),'i6'), #lon
           ((33,33),'a1'), #E or W
           ((34,37),'i4'), #depth
           ((38,38),'a1'), #depth quality (A, D, G, N, * or ?)
           ((39,40),'i2'), #num depth phases (saturates at 99)
           ((41,43),'i3'), #num P or PKP arrivals
           ((44,46),'i3'), #std dev
           ((47,47),'a1'),#quality flag (&, *, % or ?)
           ((48,49),'i2'), #MB value
           ((50,51),'i2'), #number of amplitudes (saturates at 99)
           ((52,53),'i2'), #Ms value
           ((54,55),'i2'), #number of amps used (saturates at 99)
           ((56,56),'a1'), #component
           ((57,59),'i3'), #magnitude
           ((60,61),'a2'),#magtype
           ((62,66),'a5',0,1),#contributor
           ((67,69),'i3'), #mag 2
           ((70,71),'a2'),#magtype 2
           ((72,76),'a5',0,1),#contributor 2
           ((77,79),'i3'), #FE number
           ((80,80),'a1'), #max MMI
           ((81,81),'a1'), #macroseismic (H=heard, F=felt, D=damage, C=casualties)
           ((82,82),'a1'), #moment tensor (any source) published in monthly listing (M)
           ((83,83),'a1'), #isoseismal/intensity map (P = PDE or Monthly Listing or U = U.S. Earthquakes)
           ((84,84),'a1'),#GS fault plane solution (F)
           ((85,85),'a1'),#IDE event (X) -- prior to PDE 01, 2004 event quality flag (A,B,C,D,H,N) -- begin with PDE 01, 2004
           ((86,86),'a1'),#diastrophic phenomena (U = uplift, S = subsidence, F = faulting, 3 = U & S, 4 = U & F, 5 = S & F, 6 = all)
           ((87,87),'a1'),#tsunami (T or Q)
           ((88,88),'a1'),#seiche (S or Q)
           ((89,89),'a1'),#volcanism (V)
           ((90,90),'a1'),#non-tectonic source (E = explosion, I = collapse,C = coalbump or rockburst in coal mine, R = rockburst,M = meteoritic source)
           ((91,91),'a1'),#guided waves in atmosphere/ocean (T = t wave, A = acoustic wave, G = gravity wave, B = gravity and acoustic waves, M = multiple effects)
           ((92,92),'a1'),#ground, soil, water table and atmospheric phenomena (L = liquefaction, G = geyser, S = landslide/avalanche,B = sand blows, C = ground cracks not known to be an expression of faulting, V = visual/lights,O = unusual odors, M = multiple effects)
           ((93,93),'a1'), #<
           ((94,98),'a5'), #contributor
           ((99,99),'a1')] #>

EHDF_EVENT_TYPES = {'explosion':'E','collapse':'I','rock burst':'R','meteorite':'M'}

class PhaseML(object):
    def __init__(self):
        self.AmpKeys = []

    def readFromFile(self,xmlfile):
        data = open(xmlfile,'rt').read()
        self.readFromString(data)

    def readFromString(self,data,url=None):
        root = parseString(data)
        self.url = url
        self.event = root.getElementsByTagName('event')[0]
        self.eventcode = self.event.getAttribute('catalog:dataid')
        self.getPicks() #sets self.picks
        self.getArrivals() #sets self.arrivals
        self.EventType = self.getEventType()
        self.getOrigins() #sets self.prefid,self.origins
        self.getFERegion(self.preferredOrigin['lat'],self.preferredOrigin['lon']) #sets self.location and self.FENumber
        self.getAmplitudes() #sets self.amplitudes
        self.getStationMagnitudes() #sets self.stationMagnitudes
        self.getMagnitudes() #sets self.magnitudes
        self.getTensors() #sets self.tensors
        self.getPhases() #sets self.phases - combines pick, arrival, amplitude and stationMagnitude
        root.unlink()
        
    def renderISF(self):
        isf = 'BEGIN IMS1.0\n'
        isf += 'MSG_TYPE DATA\n'
        isf += 'MSG_ID %s\n' % self.eventcode.upper()
        isf += 'DATA_TYPE BULLETIN IMS2.0:SHORT\n'
        preforigin = self.preferredOrigin
        if preforigin['analysistype'] == 'm':
            isf += 'The following is a MANUALLY REVIEWED LOCATION from the USGS/NEIC National Seismic Network System\n'
        else:
            isf += 'The following is an AUTOMATICALLY REVIEWED LOCATION from the USGS/NEIC National Seismic Network System\n'
        
        isf += 'Event   %s %s\n\n' % (self.eventcode.upper(),self.location)

        #if there is a url field, render that as a comment.  This should help with QA/QC
        if self.url is not None:
            isf += ' (%s)' % self.url
            isf += '\n\n'

        #render the origin block
        hdrvalues = ('Date','Time','Err','RMS','Latitude','Longitude',
                   'Smaj','Smin','Az','Depth','Err','Ndef','Nst',
                   'Gap','mdist','Mdist','Qual','Author','OrigID')
        line = fixed.getFixedFormatString(ORIGINHDR,hdrvalues)
        isf += line+'\n'
        for o in self.origins:
            if not np.isnan(o['semimajor']):
                isFixed = True
                if o['depthtype'].lower().find('from location') > -1 or o['depthtype'].strip() == '':
                    isFixed = False
                semimajor,semiminor,majorazimuth = ellipse.tait2surface(o['semimajor'],
                                                                        o['semiminor'],
                                                                        o['intermediateaxis'],
                                                                        o['majorazimuth'],
                                                                        o['majorplunge'],
                                                                        o['majorrotation'],
                                                                        o['numphases'],
                                                                        o['originrms'],
                                                                        False)
            else:
                semimajor = semiminor = majorazimuth = np.nan
                
            second = o['time'].second + o['time'].microsecond/1e6
            vlist = [o['time'].year,'/',o['time'].month,'/',o['time'].day,
            o['time'].hour,':',o['time'].minute,':',second,o['timefixed'],
            o['time_error'],o['originrms'],o['lat'],o['lon'],o['epifixed'],semimajor,
            semiminor,majorazimuth,o['depth'],o['depthfixed'],o['deptherr'],
            o['numphases'],o['numstations'],o['azgap'],o['mindist'],o['maxdist'],
            o['analysistype'],o['locmethod'],o['event_type'],o['author'],' ']
            line = fixed.getFixedFormatString(ORIGINFMT,vlist)
            isf += line+'\n'

        isf += '\n'

        #render the magnitude block
        line = fixed.getFixedFormatString(MAGHDR,['Magnitude','Err','Nsta','Author','OrigID'])
        isf += line + '\n'
        for m in self.magnitudes:
            vlist = [m['magtype'],' ',m['magnitude'],m['magerr'],m['nstations'],m['author'],m['dataid']]
            line = fixed.getFixedFormatString(MAGFMT,vlist)
            isf += line+'\n'

        #render the moment tensor comment block
        isf += '\n'
        for m in self.tensors:
            line = fixed.getFixedFormatString(MOMENTHDR1,MOMENTLBL1)
            isf += line+'\n'
            line = fixed.getFixedFormatString(MOMENTHDR2,MOMENTLBL2)
            isf += line+'\n'
            vlist = ['(','#',m['exponent'],m['scalarmoment'],m['fclvd'],
                     m['mrr'],m['mtt'],m['mpp'],m['mrt'],m['mtp'],m['mrp'],
                     m['nbodystations'],m['nsurfacestations'],m['dataid']]
            line = fixed.getFixedFormatString(MOMENTFMT1,vlist)
            isf += line + '\n'
            vlist = ['(','#',m['momenterror'],m['clvderror'],
                     m['mrrerror'],m['mtterror'],m['mpperror'],
                     m['mrterror'],m['mrperror'],m['mtperror'],
                     m['nbodycomp'],m['nsurfacecomp'],m['duration']]
            line = fixed.getFixedFormatString(MOMENTFMT2,vlist)
            isf += line + '\n'

        isf += '\n'
            
        #render the phase block
        line = fixed.getFixedFormatString(PHASEHDR,PHASELBL)
        isf += line + '\n'
        for p in self.phases:
            stacode = p['station']
            second = p['time'].second + p['time'].microsecond/1e6
            vlist = [stacode,p['distance'],p['stationazimuth'],p['phasetype'],
                     p['time'].hour,':',p['time'].minute,':',second,p['timeres'],
                     p['azimuth'],p['azres'],p['slowness'],p['slowres'],p['timeflag'],
                     p['azflag'],p['slowflag'],p['snr'],p['amplitude'],p['period'],
                     p['picktype'],p['direction'],p['quality'],p['magtype'],
                     p['minmax'],p['mag'],p['arrid']]
            line = fixed.getFixedFormatString(PHASEFMT,vlist)
            isf += line+'\n'

        isf += '\n'
        
        isf += 'STOP\n'
        
        return isf

    def getEHDFMagAndSource(self,qtype,qsrc):
        etype = ''
        esrc = ''
        smax = min(len(qsrc),5)
        if qtype.lower() == 'mw':
            etype = 'MW'
            esrc = qsrc.upper()
        if qtype.lower() == 'mww':
            etype = 'MW'
            esrc = 'WCMT'
        if qtype.lower() == 'mwc':
            etype = 'MW'
            if qsrc.lower() == 'gcmt':
                esrc = 'GCMT'
            elif qsrc.lower() == 'us':
                esrc = 'UCMT'
            else:
                esrc = qsrc.upper()
        if qtype.lower() == 'mwb':
            etype = 'MW'
            esrc = 'UBMT'
        if qtype.lower() == 'mb':
            etype = 'MB'
            esrc = qsrc[0:smax].upper()
        if qtype.lower() == 'ms_20':
            etype = 'MS'
            esrc = 'US'
        if qtype.lower() == 'mwr':
            etype = 'MW'
            if qsrc.lower() == 'us':
                esrc = 'URMT'
            else:
                esrc = qsrc.upper()
        if qtype.lower() == 'ml':
            etype = 'ML'
            esrc = qsrc.upper()
        if qtype.lower() == 'md':
            etype = 'MD'
            esrc = qsrc.upper()
        if qtype.lower() == 'mb_lg':
            etype = 'LG'
            esrc = qsrc.upper()

        if len(esrc) > 5:
            if esrc.find('US_') > -1:
                esrc = esrc.replace('US_','')
            esrc = esrc[0:min(5,len(esrc))]
        return (etype,esrc)
        
    
    def renderEHDF(self):
        magtrans = {'Mww':'MW',
                    'Mwb':'MW',
                    'Mwc':'MW',
                    'Ms_20':'MS',
                    'Mb':'MB'} #magnitude translation table to get to 2 character magnitude types
        preforigin = self.preferredOrigin
        yr,mo,da,hr,mi,se,th = self.getTimePieces(preforigin['time'])
        lat = preforigin['lat']
        lon = preforigin['lon']
        lat,NS,lon,EW = self.getLatLon(lat,lon)
        lat = int(lat * 1000)
        lon = int(lon * 1000)
        dep = int(preforigin['depth']*10)
        depthtype = preforigin['depthtype']
        #Depth type fields are:
        # from location
        # from moment tensor inversion
        # from from modeling of broad-band P waveforms
        # constrained by depth phases
        # constrained by direct phases
        # constrained by depth and direct phases
        # operator assigned
        # other.
        if depthtype.find('operator') > -1:
            depflag = 'G'
        else:
            deptherror = preforigin['deptherr']
            if not math.isnan(deptherror):
                if deptherror > 8.5 and deptherror <= 16.0:
                    depflag = '*'
                elif deptherror > 16.0:
                    depflag = '?'
                else:
                    depflag = ' '
            else:
                depflag = ' '
        nump = preforigin['numphases'] #these are the number of phases for the hypocenter... ok
        numdep = float('nan')
        std = float('nan')
        #assign hypocenter quality
        axesmean = math.sqrt(preforigin['semimajor'] * preforigin['semiminor'])
        if axesmean <= 8.5:
            hypq = '%'
        elif axesmean > 8.5 and axesmean <= 16.0:
            hypq = '*'
        else:
            hypq = '?'
        magmb = float('nan')
        magmbsta = float('nan')
        magms = float('nan')
        magmssta = float('nan')
        magmscomp = 'Z'
        mag1 = float('nan') #contrib mag 1
        mag2 = float('nan') #contrib mag 2
        mag1t = '' #contrib mag 1 type
        mag2t = '' #contrib mag 2 type
        mag1s = '' #contrib mag 1 source
        mag2s = '' #contrib mag 2 source
        magtypes = [mag['magtype'].lower() for mag in self.magnitudes]
        #Ms magnitudes may be represented as Ms_20 or something similar
        #just assume that anything starting with "ms" is an Ms.
        for i in range(0,len(magtypes)):
            mag = magtypes[i]
            if mag.startswith('ms'):
                magtypes[i] = 'ms'
        copymags = copy.copy(self.magnitudes)
        mag1,mag1t,mag1s,idx = self.getEHDFMagnitude(copymags)
        if idx >= 0:
            copymags.pop(idx)
        mag2,mag2t,mag2s,idx = self.getEHDFMagnitude(copymags)
        if idx >= 0:
            copymags.pop(idx)
        if 'mb' in magtypes:
            idx = magtypes.index('mb')
            magmb = int(self.magnitudes[idx]['magnitude']*10)
            magmbsta = self.magnitudes[idx]['nstations']
            if magmbsta > 99:
                magmbsta = 99
        if 'ms' in magtypes:
            idx = magtypes.index('ms')
            magms = int(self.magnitudes[idx]['magnitude']*10)
            magmssta = self.magnitudes[idx]['nstations']
            if magmssta > 99:
                magmssta = 99

        #print 'Before translation: Mag1 type = %s, source = %s' % (mag1t,mag1s)
        mag1t,mag1s = self.getEHDFMagAndSource(mag1t,mag1s)
        #print 'After translation: Mag1 type = %s, source = %s' % (mag1t,mag1s)
        #print 'Before translation: Mag2 type = %s, source = %s' % (mag2t,mag2s)
        mag2t,mag2s = self.getEHDFMagAndSource(mag2t,mag2s)
        #print 'After translation: Mag2 type = %s, source = %s' % (mag2t,mag2s)
        
        fenum = self.FENumber
        maxmi = '' #blank is unknown value
        #putting blanks for all flags for now - get Paul to fill in
        msflag = ''
        mtflag = ''
        if len(self.tensors):
            mtflag = 'M'
    
        iiflag = '' #??
        fpflag = '' #??
        ieflag = ''
        dpflag = ''
        tsflag = ''
        seflag = ''
        voflag = ''
        ntflag = ''
        if self.EventType in EHDF_EVENT_TYPES.keys():
            ntflag = EHDF_EVENT_TYPES[self.EventType]
        gwflag = ''
        gpflag = ''
        author = '%-5s' % (preforigin['author'])
        if len(author) > 5:
            author = author[0:5]
        if author.lower().startswith('us'): #neic solutions author should be left blank
            author = ' '*5
        vlist = ['GS','',yr,mo,da,hr,mi,se,th,lat,NS,lon,EW,dep,depflag,numdep,nump,std,hypq,
                 magmb,magmbsta,magms,magmssta,magmscomp,mag1,mag1t,mag1s,mag2,mag2t,mag2s,
                 fenum,maxmi,msflag,mtflag,iiflag,fpflag,ieflag,dpflag,tsflag,seflag,voflag,
                 ntflag,gwflag,gpflag,'<',author,'>']
        try:
            line = fixed.getFixedFormatString(EHDRFMT,vlist)
            return line
        except Exception,msg:
            sys.stderr.write('Could not create line for %s - error "%s"\n' % (self.eventcode,msg.message))
            return None
    
    def getPhases(self):
        #combine picks, arrivals, amplitudes and stationMagnitudes into a list of phase dictionaries
        self.phases = []
        #phase has: station,distance,stationazimuth,phasetype,
        #           time,timeres,azimuth,azres,slowness,slowres,timeflag,
        #           azflag,slowflag,snr,amplitude,period,
        #           picktype,direction,quality,magtype,minmax,mag,arrid
        for pickid in self.picks.keys():
            pdict = {}
            pick = self.picks[pickid]
            if not self.arrivals.has_key(pickid):
                continue
            arrival = self.arrivals[pickid]
            pdict['station'] = pick['nscl'].split('.')[1]
            pdict['distance'] = arrival['distance']
            pdict['stationazimuth'] = arrival['azimuth']
            pdict['phasetype'] = arrival['phase']
            pdict['time'] = pick['time']
            pdict['timeres'] = arrival['timeresidual']
            pdict['azimuth'] = float('nan')
            pdict['azres'] = float('nan')
            pdict['slowness'] = float('nan')
            pdict['slowres'] = float('nan')
            pdict['timeflag'] = 'T'
            pdict['azflag'] = '_'
            pdict['slowflag'] = '_'
            pdict['snr'] = float('nan')
            pdict['amplitude'] = float('nan')
            pdict['period'] = float('nan')
            pdict['picktype'] = pick['mode'][0]
            pdict['direction'] = '_'
            pdict['quality'] = '_'
            pdict['magtype'] = ' '
            pdict['minmax'] = ' '
            pdict['mag'] = float('nan')
            pdict['nscl'] = pick['nscl']
            pdict['arrid'] = ' '
            self.phases.append(pdict.copy())
            #now we need to find all of other kind of phase - the ones with amplitude and magnitude
            magphases = self.getMagPhases(pick['nscl'],arrival['distance'],arrival['azimuth'])
            self.phases += magphases
            self.phases = sorted(self.phases,key = lambda k: (k['distance'],k['time']))

    def getMagPhases(self,nscl,distance,azimuth):
        phases = []
        for amplitude in self.amplitudes:
            if amplitude['nscl'] != nscl:
                continue
            pdict = {}
            ampid = amplitude['ampid']
            pdict['station'] = amplitude['nscl'].split('.')[1]
            pdict['distance'] = distance
            pdict['stationazimuth'] = azimuth
            pdict['timeres'] = float('nan')
            pdict['azimuth'] = float('nan')
            pdict['azres'] = float('nan')
            pdict['slowness'] = float('nan')
            pdict['slowres'] = float('nan')
            pdict['timeflag'] = '_'
            pdict['azflag'] = '_'
            pdict['slowflag'] = '_'
            pdict['snr'] = float('nan')
            pdict['phasetype'] = 'I'+amplitude['type']
            pdict['amplitude'] = amplitude['amplitude']*1e9
            pdict['period'] = amplitude['period']
            pdict['picktype'] = amplitude['mode'][0]
            ampkey = pdict['station']+pdict['picktype']
            if ampkey in self.AmpKeys:
                continue
            pdict['direction'] = '_'
            pdict['quality'] = '_'
            pdict['mag'] = self.stationMagnitudes[ampid]['magnitude']
            pdict['magtype'] = self.stationMagnitudes[ampid]['magtype']
            pdict['minmax'] = ' '
            pdict['arrid'] = ' '
            pdict['time'] = amplitude['time']
            phases.append(pdict)
            self.AmpKeys.append(ampkey)
        return phases
            
            
    def getTimePieces(self,time):
        yr = time.year
        mo = time.month
        da = time.day
        hr = time.hour
        mi = time.minute
        se = time.second
        th = int(float(time.microsecond)/1e4)        
        return (yr,mo,da,hr,mi,se,th)

    def getLatLon(self,lat,lon):
        NS = 'N'
        if lat < 0:
            NS = 'S'
            lat = abs(lat)
        EW = 'E'
        if lon < 0:
            EW = 'W'
            lon = abs(lon)
        return (lat,NS,lon,EW)

    def getEHDFMagnitude(self,maglist):
        magtypes = [mag['magtype'].lower() for mag in maglist]
        for i in range(0,len(magtypes)):
            mag = magtypes[i]
            if mag.startswith('ms'):
                magtypes[i] = 'ms'
        hierarchy = ['mww','mwr','mwb','mwc','mw','ml','lg','rg','md','cl','mg']
        mag = float('nan')
        magtype = ''
        magsrc = ''
        midx = -1
        for mtype in hierarchy:
            if mtype in magtypes:
                midx = magtypes.index(mtype)
                mag = int(maglist[midx]['magnitude']*100)
                magtype = maglist[midx]['magtype']
                magsrc = maglist[midx]['author']
                break
        if magtype == '':
            for mtype in magtypes:
                if mtype not in ['mb','ms']:
                    midx = magtypes.index(mtype)
                    mag = int(maglist[midx]['magnitude']*100)
                    magtype = maglist[midx]['magtype']
                    magsrc = maglist[midx]['author']
                    break
                    
        return (mag,magtype,magsrc,midx)

    def getFERegion(self,lat,lon):
        """
        Return the FE region number, or NaN if it cannot be found.
        lat: Latitude of input point.
        lat: Latitude of input point.
        Returns FE region number.
        """
        url = 'http://geohazards.cr.usgs.gov/cfusion/fe_regions.cfc?method=getRegion&lat=LAT&lon=LON'
        url = url.replace('LAT',str(lat))
        url = url.replace('LON',str(lon))
        locnum = float('nan')
        locstr = '%.4f,%.4f' % (lat,lon)
        try:
            fh = urllib2.urlopen(url)
            regstr = fh.read()
            fh.close()
            parts = regstr.split('|')
            locnum = int(parts[0].strip())
            locstr = parts[3].strip()
        except:
            pass

        self.location = locstr
        self.FENumber = locnum

    def getTensorMetadata(self,tensor):
        m0 = float(tensor.getElementsByTagName('scalarMoment')[0].getElementsByTagName('value')[0].firstChild.data)
        if len(tensor.getElementsByTagName('clvd')):
            fclvd = float(tensor.getElementsByTagName('clvd')[0].firstChild.data)
            if fclvd > 1:
                fclvd = fclvd/100.0
        else:
            fclvd = float('nan')
    
        exponent = math.floor(math.log10(m0))
        scalarMoment = m0/math.pow(10,exponent)
        return (m0,exponent,fclvd,scalarMoment)

    def getTensorComponents(self,tensor,exponent):
        if len(tensor.getElementsByTagName('tensor')):
            tensorel = tensor.getElementsByTagName('tensor')[0]
        else:
            return {'Mrr':(float('nan'),float('nan')),
                    'Mtt':(float('nan'),float('nan')),
                    'Mpp':(float('nan'),float('nan')),
                    'Mrt':(float('nan'),float('nan')),
                    'Mrp':(float('nan'),float('nan')),
                    'Mtp':(float('nan'),float('nan'))}
        compdict = {}
        for component in ['Mrr','Mtt','Mpp','Mrt','Mrp','Mtp']:
            comp = tensor.getElementsByTagName(component)[0]
            value = float(comp.getElementsByTagName('value')[0].firstChild.data)/math.pow(10,exponent)
            if len(comp.getElementsByTagName('uncertainty')):
                error = float(comp.getElementsByTagName('uncertainty')[0].firstChild.data)/math.pow(10,exponent)
            else:
                error = float('nan')
            compdict[component] = (value,error)
        return compdict

    def getTensorDataUsed(self,tensor):
        #return number of stations and components used
        #p-waves and mantle waves are both defined here as being body waves
        #find the number of components used
        nbodycomponents = 0
        nsurfacecomponents = 0
        nbodystations = 0
        nsurfacestations = 0
        if len(tensor.getElementsByTagName('dataUsed')):
            for dataused in tensor.getElementsByTagName('dataUsed'):
                wavetype = dataused.getElementsByTagName('waveType')[0].firstChild.data
                if wavetype == 'surface':
                    if len(dataused.getElementsByTagName('componentCount')):
                        nsurfacecomponents += int(dataused.getElementsByTagName('componentCount')[0].firstChild.data)
                    if len(dataused.getElementsByTagName('stationCount')):
                        nsurfacestations += int(dataused.getElementsByTagName('stationCount')[0].firstChild.data)
                else:
                    if len(dataused.getElementsByTagName('componentCount')):
                        nbodycomponents += int(dataused.getElementsByTagName('componentCount')[0].firstChild.data)
                    if len(dataused.getElementsByTagName('stationCount')):
                        nbodystations += int(dataused.getElementsByTagName('stationCount')[0].firstChild.data)

        return (nbodycomponents,nsurfacecomponents,nbodystations,nsurfacestations)

    def getDataID(self,dataid):
        #we need to munge the dataid a little bit to get it down below 8 characters (hopefully)
        #dataid values can look like this: "us_c000lvb5_mww", or "us_c000lvb5_mwc_gcmt".
        #in the first case we want "us_mww", and in the second we want "gcmt_mwc".
        #first, split the dataid into pieces:
        parts = dataid.split('_')
        mtypes = ['mww','mwc','mwb','mwr','mb']
        networks = ['us','ak','ci','nc','hv','uu','ld','pn','pr','gcmt']
        network = None
        mtype = None
        for part in parts:
            if part in mtypes:
                mtype = part
            if part in networks:
                network = part #since gcmt is at the end, this should trump us
        if len('%s_%s' % (network,mtype)) > 8:
            dataid = mtype
        else:
            dataid = '%s_%s' % (network,mtype)
        return dataid
            
    def getTensors(self):
        self.tensors = []
        mechs = self.event.getElementsByTagName('focalMechanism')
        for mech in mechs:
            dataid = self.getDataID(mech.getAttribute('catalog:dataid'))
            for tensor in mech.getElementsByTagName('momentTensor'):
                m0,exponent,fclvd,scalarMoment = self.getTensorMetadata(tensor)
                compdict = self.getTensorComponents(tensor,exponent)
                nbodycomp,nsurfacecomp,nbodystations,nsurfacestations = self.getTensorDataUsed(tensor)
                #Get the duration, if provided
                sourcetimelist = tensor.getElementsByTagName('sourceTimeFunction')
                if len(sourcetimelist):
                    duration = float(sourcetimelist[0].getElementsByTagName('duration')[0].firstChild.data)
                else:
                    duration = float('nan')

                #get the author
                if len(tensor.getElementsByTagName('creationInfo')):
                    creationinfo = tensor.getElementsByTagName('creationInfo')[0]
                    author = creationinfo.getElementsByTagName('agencyID')[0].firstChild.data
                else:
                    author = ''
                mrr,mrrerror = compdict['Mrr']
                mtt,mtterror = compdict['Mtt']
                mpp,mpperror = compdict['Mpp']
                mrt,mrterror = compdict['Mrt']
                mrp,mrperror = compdict['Mrp']
                mtp,mtperror = compdict['Mtp']
                self.tensors.append({'m0':m0,'exponent':exponent,'fclvd':fclvd,
                                     'mrr':mrr,'mtt':mtt,'mpp':mpp,
                                     'mrt':mrt,'mrp':mrp,'mtp':mtp,
                                     'mrrerror':mrrerror,'mtterror':mtterror,'mpperror':mpperror,
                                     'mrterror':mrterror,'mrperror':mrperror,'mtperror':mtperror,
                                     'nbodycomp':nbodycomp,'nsurfacecomp':nsurfacecomp,
                                     'nbodystations':nbodystations,'nsurfacestations':nsurfacestations,
                                     'duration':duration,'scalarmoment':scalarMoment,
                                     'author':author,'momenterror':float('nan'),
                                     'clvderror':float('nan'),'dataid':dataid})
        
    def getMagnitudes(self):
        self.magnitudes = []
        for mag in self.event.getElementsByTagName('magnitude'):
            magel = mag.getElementsByTagName('mag')[0]
            dataid = self.getDataID(mag.getAttribute('catalog:dataid'))
            magnitude = float(magel.getElementsByTagName('value')[0].firstChild.data)
            magtype = mag.getElementsByTagName('type')[0].firstChild.data
            if len(magel.getElementsByTagName('uncertainty')):
                magerr = float(magel.getElementsByTagName('uncertainty')[0].firstChild.data)
            else:
                magerr = float('nan')
            if len(mag.getElementsByTagName('stationCount')):
                nstations = int(mag.getElementsByTagName('stationCount')[0].firstChild.data)
            else:
                nstations = float('nan')
            if len(mag.getElementsByTagName('evaluationMode')):
                mode = mag.getElementsByTagName('evaluationMode')[0].firstChild.data
            else:
                mode = 'automatic'
            if len(mag.getElementsByTagName('evaluationStatus')):
                status = mag.getElementsByTagName('evaluationStatus')[0].firstChild.data
            else:
                status = 'preliminary'
            creationinfo = mag.getElementsByTagName('creationInfo')[0]
            if len(creationinfo.getElementsByTagName('agencyID')):
                #sometimes agencyID looks like this:
                # <creationInfo>
                # <agencyID/>
                # </creationInfo>
                if creationinfo.getElementsByTagName('agencyID')[0].firstChild is not None:
                    author = creationinfo.getElementsByTagName('agencyID')[0].firstChild.data
                    #sometimes author exceeds allotted 9 spaces, so we'll truncate here
                    author = author[0:9]
                else:
                    author = ''
            else:
                author = '' #guess the source based on information in magnitude ID
            self.magnitudes.append({'magnitude':magnitude,'magtype':magtype,'mode':mode,
                                    'status':status,'author':author,'magerr':magerr,
                                    'nstations':nstations,'magid':'','dataid':dataid})
            
        
    def getStationMagnitudes(self):
        self.stationMagnitudes = {}
        for smag in self.event.getElementsByTagName('stationMagnitude'):
            if not len(smag.getElementsByTagName('amplitudeID')):
                continue
            ampid = smag.getElementsByTagName('amplitudeID')[0].firstChild.data
            if len(smag.getElementsByTagName('originID')) and smag.getElementsByTagName('originID')[0].firstChild is not None:
                originid = smag.getElementsByTagName('originID')[0].firstChild.data
            else:
                originid = ''
            magel = smag.getElementsByTagName('mag')[0]
            try:
                magnitude = float(magel.getElementsByTagName('value')[0].firstChild.data)
            except:
                continue
            magtype = smag.getElementsByTagName('type')[0].firstChild.data
            self.stationMagnitudes[ampid] = ({'originid':originid,'magnitude':magnitude,
                                              'magtype':magtype})
            
        
    def getAmplitudes(self):
        self.amplitudes = []
        for amplitude in self.event.getElementsByTagName('amplitude'):
            units = amplitude.getElementsByTagName('unit')[0].firstChild.data
            if units.strip() != 'm':
                continue
            try:
                amptype = amplitude.getElementsByTagName('type')[0].firstChild.data
            except:
                continue #skip if there is no amplitude type information
            ampid = amplitude.getAttribute('publicID')
            try:
                generic = amplitude.getElementsByTagName('genericAmplitude')[0]
                ampvalue = float(generic.getElementsByTagName('value')[0].firstChild.data)
                amptype = amplitude.getElementsByTagName('type')[0].firstChild.data
                if len(amplitude.getElementsByTagName('period')):
                    periodel = amplitude.getElementsByTagName('period')[0]
                    period = float(periodel.getElementsByTagName('value')[0].firstChild.data)
                else:
                    period = float('nan')
                if not len(amplitude.getElementsByTagName('timeWindow')):
                    continue
                timewindow = amplitude.getElementsByTagName('timeWindow')[0]
                timestr = timewindow.getElementsByTagName('reference')[0].firstChild.data
                time = self.parseTime(timestr)
                waveform = amplitude.getElementsByTagName('waveformID')[0]
                nc = waveform.getAttribute('networkCode')
                sta = waveform.getAttribute('stationCode')
                comp = waveform.getAttribute('channelCode')
                loc = waveform.getAttribute('locationCode')
                nscl = '%s.%s.%s.%s' % (nc,sta,loc,comp)
                maghint = amplitude.getElementsByTagName('magnitudeHint')[0].firstChild.data
                mode = amplitude.getElementsByTagName('evaluationMode')[0].firstChild.data
            except:
                pass
            self.amplitudes.append({'amplitude':ampvalue,'type':amptype,'period':period,
                                     'nscl':nscl,'time':time,'maghint':maghint,'ampid':ampid,
                                     'mode':mode})
            
        
    def getArrivals(self):
        self.arrivals = {}
        for origin in self.event.getElementsByTagName('origin'):
            originid = origin.getAttribute('publicID')
            for arrival in origin.getElementsByTagName('arrival'):
                pickid = arrival.getElementsByTagName('pickID')[0].firstChild.data
                phase = arrival.getElementsByTagName('phase')[0].firstChild.data
                azimuth = float(arrival.getElementsByTagName('azimuth')[0].firstChild.data)
                if len(arrival.getElementsByTagName('distance')):
                    distance = float(arrival.getElementsByTagName('distance')[0].firstChild.data)
                else:
                    continue
                timeresidual = float(arrival.getElementsByTagName('timeResidual')[0].firstChild.data)
                if len(arrival.getElementsByTagName('creationInfo')):
                    creationinfo = arrival.getElementsByTagName('creationInfo')[0]
                    if len(creationinfo.getElementsByTagName('author')):
                        author = creationinfo.getElementsByTagName('author')[0].firstChild.data
                    else:
                        author = ''
                else:
                    author = ''
                self.arrivals[pickid] = {'phase':phase,'azimuth':azimuth,'distance':distance,
                                         'timeresidual':timeresidual,'author':author,'originid':originid}
            
    def parseTime(self,timestr):
        timestr = timestr.rstrip('Z')
        if len(timestr) > 19:
            time = datetime.datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%S.%f')
        else:
            time = datetime.datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%S')
        return time
        
    def getPicks(self):
        self.picks = {}
        for pick in self.event.getElementsByTagName('pick'):
            pickid = pick.getAttribute('publicID')
            timestr = pick.getElementsByTagName('time')[0].getElementsByTagName('value')[0].firstChild.data
            time = self.parseTime(timestr)
            waveform = pick.getElementsByTagName('waveformID')[0]
            nc = waveform.getAttribute('networkCode')
            sta = waveform.getAttribute('stationCode')
            comp = waveform.getAttribute('channelCode')
            loc = waveform.getAttribute('locationCode')
            nscl = '%s.%s.%s.%s' % (nc,sta,comp,loc)
            if len(pick.getElementsByTagName('creationInfo')):
                creationinfo = pick.getElementsByTagName('creationInfo')[0]
                author = creationinfo.getElementsByTagName('agencyID')[0].firstChild.data
            else:
                author = ''
            mode = pick.getElementsByTagName('evaluationMode')[0].firstChild.data
            self.picks[pickid] = {'time':time,'nscl':nscl,'author':author,'mode':mode}
        
    def getEventType(self):
        etype = 'earthquake'
        for c in self.event.childNodes:
            if c.nodeType == c.ELEMENT_NODE and c.tagName == 'type':
                etype = c.firstChild.data
                break
        return etype
        
    def getOrigins(self):
        self.prefid = self.event.getElementsByTagName('preferredOriginID')[0].firstChild.data
        self.origins = []
        idx = 0
        for origin in self.event.getElementsByTagName('origin'):
            publicid = origin.getAttribute('publicID')
            orig = self.getOrigin(origin)
            if orig is not None:
                self.origins.append(orig.copy())
                if orig['publicid'] == self.prefid:
                    self.preferredOrigin = orig.copy()

            
    def getOrigin(self,origin):
        originid = origin.getAttribute('catalog:eventid')
        publicid = origin.getAttribute('publicID')
        if not len(origin.getElementsByTagName('time')):
            return None
        timestr = origin.getElementsByTagName('time')[0].getElementsByTagName('value')[0].firstChild.data
        time = self.parseTime(timestr)
        timeel = origin.getElementsByTagName('time')[0]
        if len(timeel.getElementsByTagName('uncertainty')):
            errortime = float(timeel.getElementsByTagName('uncertainty')[0].firstChild.data)
        else:
            errortime = float('nan')
        lat = float(origin.getElementsByTagName('latitude')[0].getElementsByTagName('value')[0].firstChild.data)
        lon = float(origin.getElementsByTagName('longitude')[0].getElementsByTagName('value')[0].firstChild.data)
        depth = float(origin.getElementsByTagName('depth')[0].getElementsByTagName('value')[0].firstChild.data)/1000.0
        depthel = origin.getElementsByTagName('depth')[0]
        if len(origin.getElementsByTagName('depthType')):
            depthtype = origin.getElementsByTagName('depthType')[0].firstChild.data
        else:
            depthtype = ''
        if len(depthel.getElementsByTagName('uncertainty')):
            deptherr = float(depthel.getElementsByTagName('uncertainty')[0].firstChild.data)/1000.0
        else:
            deptherr = float('nan')
        if len(origin.getElementsByTagName('quality')):
            if len(origin.getElementsByTagName('quality')[0].getElementsByTagName('standardError')):
                rms = float(origin.getElementsByTagName('quality')[0].getElementsByTagName('standardError')[0].firstChild.data)
            else:
                rms = float('nan')
            if len(origin.getElementsByTagName('quality')[0].getElementsByTagName('usedPhaseCount')):
                ndef = int(origin.getElementsByTagName('quality')[0].getElementsByTagName('usedPhaseCount')[0].firstChild.data)
            else:
                ndef = len(origin.getElementsByTagName('arrival'))
                if not ndef:
                    ndef = float('nan')
            if len(origin.getElementsByTagName('quality')[0].getElementsByTagName('azimuthalGap')):
                azgap = float(origin.getElementsByTagName('quality')[0].getElementsByTagName('azimuthalGap')[0].firstChild.data)
            else:
                azgap = float('nan')
        else:
            rms = float('nan')
            ndef = float('nan')
            azgap = float('nan')

        nst,mindist,maxdist = self.getStationInfo(origin)

        timefixed = ' '
        epifixed = ' '
        depthfixed = ' '
        if len(origin.getElementsByTagName('creationInfo')):
            author = origin.getElementsByTagName('creationInfo')[0].getElementsByTagName('agencyID')[0].firstChild.data.upper()
            #because ISF only allows 9 spaces for the "author" field in an origin block, we have to truncate here
            author = author[0:9]
        else:
            author = ''
        if len(origin.getElementsByTagName('evaluationMode')):
            status = origin.getElementsByTagName('evaluationMode')[0].firstChild.data
        else:
            status = 'automatic'
        if status == 'manual':
            status = 'm'
        else:
            status = 'a'
        locmethod = ''
        # if len(origin.getElementsByTagName('type')):
        #     event_type = origin.getElementsByTagName('type')[0].firstChild.data
        # else:
        #     event_type = 'earthquake'

        if self.EventType == 'earthquake':
            event_type = 'ke'
        else:
            event_type = 'se'
        #get the elements of the confidence ellipsoid, if present
        majoraxis = float('nan')
        minoraxis = float('nan')
        intermediateaxis = float('nan')
        majorplunge = float('nan')
        majorazimuth = float('nan')
        majorrotation = float('nan')
        if len(origin.getElementsByTagName('confidenceEllipsoid')):
            ellipse = origin.getElementsByTagName('confidenceEllipsoid')[0]
            majoraxis = float(ellipse.getElementsByTagName('semiMajorAxisLength')[0].firstChild.data)/1000 #now in km
            minoraxis = float(ellipse.getElementsByTagName('semiMinorAxisLength')[0].firstChild.data)/1000 #now in km
            intermediateaxis = float(ellipse.getElementsByTagName('semiIntermediateAxisLength')[0].firstChild.data)/1000 #now in km
            majorplunge = float(ellipse.getElementsByTagName('majorAxisPlunge')[0].firstChild.data)
            majorazimuth = float(ellipse.getElementsByTagName('majorAxisAzimuth')[0].firstChild.data)
            majorrotation = float(ellipse.getElementsByTagName('majorAxisRotation')[0].firstChild.data)
        
        
        orig = {'time':time,'timefixed':timefixed,'time_error':errortime,'originrms':rms,'lat':lat,'lon':lon,
                'epifixed':epifixed,
                'semimajor':majoraxis,'semiminor':minoraxis,'intermediateaxis':intermediateaxis,
                'majorplunge':majorplunge,'majorazimuth':majorazimuth,'majorrotation':majorrotation,
                'depth':depth,'depthfixed':depthfixed,'deptherr':deptherr,'numphases':ndef,'numstations':nst,
                'azgap':azgap,'mindist':mindist,'maxdist':maxdist,'analysistype':status,
                'locmethod':locmethod,'event_type':event_type,'author':author,'originid':originid,
                'publicid':publicid,'depthtype':depthtype}
        return orig

    def getStationInfo(self,origin):
        originid = origin.getAttribute('publicID')
        stations = []
        mindist = 99999999999999
        maxdist = -99999999999999
        for pickid in self.arrivals.keys():
            arrival = self.arrivals[pickid]
            if arrival['originid'] != originid:
                continue
            station = self.picks[pickid]['nscl']
            if station not in stations:
                stations.append(station)
            if arrival['distance'] > maxdist:
                maxdist = arrival['distance']
            if arrival['distance'] < maxdist:
                mindist = arrival['distance']
        if mindist == 99999999999999:
            mindist = float('nan')
            maxdist = float('nan')
        return (len(stations),mindist,maxdist)
            
        arrivals = origin.getElementsByTagName('arrival')
        stations = []
        mindist = 99999999999999
        maxdist = -99999999999999
        for arrival in arrivals:
            arrid = arrival.getElementsByTagName('pickID')[0].firstChild.data
            station = None
            for pick in picks:
                pickid = pick.getAttribute('publicID')
                if pickid == arrid:
                    station = getNSCL(pick.getElementsByTagName('waveformID')[0])
                    break
            if station is None:
                continue
            if station not in stations:
                stations.append(station)
            adist = float(arrival.getElementsByTagName('distance')[0].firstChild.data)
            if adist < mindist:
                mindist = adist
            if adist > maxdist:
                maxdist = adist
        return (len(stations),mindist,maxdist)
    
if __name__ == '__main__':
    xmlfile = sys.argv[1]
    phaseml = PhaseML()
    phaseml.readFromFile(xmlfile)
    isf = phaseml.renderISF()
    print isf
    ehdf = phaseml.renderEHDF()
    print 
    print ehdf
        
    
