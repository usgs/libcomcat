#stdlib imports
from xml.dom import minidom
import sys
from urllib import request

#third party imports
import numpy as np
import pandas as pd
from impactutils.time.ancient_time import HistoricTime

#constants
CATALOG_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/catalogs'
CONTRIBUTORS_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/contributors'
TIMEOUT = 60
TIMEFMT1 = '%Y-%m-%dT%H:%M:%S'
TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'
DATEFMT = '%Y-%m-%d'

def makedict(dictstring):
    try:
        parts = dictstring.split(':')
        key = parts[0]
        value = parts[1]
        return {key:value}
    except:
        raise Exception('Could not create a single key dictionary out of %s' % dictstring)

def maketime(timestring):
    outtime = None
    try:
        outtime = HistoricTime.strptime(timestring,TIMEFMT1)
    except:
        try:
            outtime = HistoricTime.strptime(timestring,TIMEFMT2)
        except:
            try:
                outtime = HistoricTime.strptime(timestring,DATEFMT)
            except:
                raise Exception('Could not parse time or date from %s' % timestring)
    return outtime



def get_catalogs():
    """Get the list of catalogs available in ComCat.

    :returns:
      List of catalogs available in ComCat (see the catalog parameter in search() method.)
    """
    fh = request.urlopen(CATALOG_SEARCH_TEMPLATE,timeout=TIMEOUT)
    data = fh.read().decode('utf8')
    fh.close()
    root = minidom.parseString(data)
    catalogs = root.getElementsByTagName('Catalog')
    catlist = []
    for catalog in catalogs:
        catlist.append(catalog.firstChild.data)
    root.unlink()
    return catlist

def get_contributors():
    """Get the list of contributors available in ComCat.

    :returns:
      List of contributors available in ComCat (see the contributor parameter in search() method.)
    """
    fh = request.urlopen(CONTRIBUTORS_SEARCH_TEMPLATE,timeout=TIMEOUT)
    data = fh.read().decode('utf8')
    fh.close()
    root = minidom.parseString(data)
    contributors = root.getElementsByTagName('Contributor')
    conlist = []
    for contributor in contributors:
        conlist.append(contributor.firstChild.data)
    root.unlink()
    return conlist

def get_detail_data_frame(events,get_all_magnitudes=False,
                          get_all_tensors=False,
                          get_all_focal=False):
    """Take the results of a search and extract the detailed event informat in a pandas DataFrame.

    Usage:
      TODO
    
    :param events:
      List of SummaryEvent objects as returned by search() function.
    :param get_all_magnitudes:
      Boolean indicating whether to return all magnitudes in results for each event.
    :param get_all_tensors:
      Boolean indicating whether to return all moment tensors in results for each event.
    :param get_all_focal:
      Boolean indicating whether to return all focal mechanisms in results for each event.
    
    :returns:  
      Pandas DataFrame with one row per event, and all relevant information in columns.
    """
    df = pd.DataFrame()
    sys.stderr.write('%i events downloaded.' % len(events))
    ic = 0
    inc = np.power(10,np.floor(np.log10(len(events)))-1)
    for event in events:
        try:
            detail = event.getDetailEvent()
        except Exception as e:
            print('Failed to get detailed version of event %s' % event.id)
            continue
        edict = detail.toDict(get_all_magnitudes=get_all_magnitudes,
                              get_all_tensors=get_all_tensors,
                              get_all_focal=get_all_focal)
        df = df.append(edict,ignore_index=True)
        if ic % inc == 0:
            msg = 'Getting detailed information for %s, %i of %i events.\n'
            sys.stderr.write(msg % (event.id,ic,len(events)))
        ic += 1
    first_columns = ['id','time','latitude','longitude','depth','magnitude']
    all_columns = df.columns
    rem_columns = [col for col in all_columns if col not in first_columns]
    new_columns = first_columns + rem_columns
    df = df[new_columns]
    return df
        
def get_summary_data_frame(events):
    """Take the results of a search and extract the summary event informat in a pandas DataFrame.

    Usage:
      TODO
    
    :param events:
      List of SummaryEvent objects as returned by search() function.
    
    :returns:  
      Pandas DataFrame with one row per event, and columns:
       - id (string) Authoritative ComCat event ID.
       - time (datetime) Authoritative event origin time.
       - latitude (float) Authoritative event latitude.
       - longitude (float) Authoritative event longitude.
       - depth (float) Authoritative event depth.
       - magnitude (float) Authoritative event magnitude.
    """
    df = pd.DataFrame(columns=events[0].toDict().keys())
    for event in events:
        edict = event.toDict()
        df = df.append(edict,ignore_index=True)
    return df
