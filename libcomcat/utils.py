# stdlib imports
from xml.dom import minidom
import sys
from urllib.request import urlopen
import warnings
from datetime import datetime
import os.path

# third party imports
import numpy as np
import pandas as pd
from obspy.io.quakeml.core import Unpickler
from impactutils.time.ancient_time import HistoricTime
from openpyxl import load_workbook

# constants
CATALOG_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/catalogs'
CONTRIBUTORS_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/contributors'
TIMEOUT = 60
TIMEFMT1 = '%Y-%m-%dT%H:%M:%S'
TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'
DATEFMT = '%Y-%m-%d'


def read_phases(filename):
    """Read a phase file CSV or Excel file into data structures.

    :param filename:
      String file name of a CSV or Excel file created by getphases program.
    :returns:
      Tuple of:
        header_dict - Dictionary containing header data from top of file.
        dataframe - Pandas dataframe containing phase data.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError('Filename %s does not exist.' % filename)
    header_dict = {}
    if filename.endswith('xlsx'):
        wb = load_workbook(filename=filename, read_only=True)
        ws = wb.active
        key = ''
        rowidx = 1

        while key != 'Channel':
            key = ws['A%i' % rowidx].value
            if not key.startswith('#'):
                value = ws['B%i' % rowidx].value
                header_dict[key] = value
            rowidx += 1
        wb.close()
        dataframe = pd.read_excel(filename, skiprows=rowidx - 2)
    elif filename.endswith('csv'):
        f = open(filename, 'rt')
        tline = f.readline()
        rowidx = 0
        while tline.startswith('#'):
            if not tline.startswith('#%'):
                line = tline.replace('#', '').strip()
                key, value = line.split('=')
                key = key.strip()
                value = value.strip()
                header_dict[key] = value
            rowidx += 1
            tline = f.readline()
        f.close()
        dataframe = pd.read_csv(filename, skiprows=rowidx)
    else:
        f, ext = os.path.splitext(filename)
        raise Exception('Filenames with extension %s are not supported.' % ext)
    return (header_dict, dataframe)


def makedict(dictstring):
    try:
        parts = dictstring.split(':')
        key = parts[0]
        value = parts[1]
        return {key: value}
    except:
        raise Exception(
            'Could not create a single key dictionary out of %s' % dictstring)


def maketime(timestring):
    outtime = None
    try:
        outtime = HistoricTime.strptime(timestring, TIMEFMT1)
    except:
        try:
            outtime = HistoricTime.strptime(timestring, TIMEFMT2)
        except:
            try:
                outtime = HistoricTime.strptime(timestring, DATEFMT)
            except:
                raise Exception(
                    'Could not parse time or date from %s' % timestring)
    return outtime


def get_catalogs():
    """Get the list of catalogs available in ComCat.

    :returns:
      List of catalogs available in ComCat (see the catalog parameter in search() method.)
    """
    fh = urlopen(CATALOG_SEARCH_TEMPLATE, timeout=TIMEOUT)
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
    fh = urlopen(CONTRIBUTORS_SEARCH_TEMPLATE, timeout=TIMEOUT)
    data = fh.read().decode('utf8')
    fh.close()
    root = minidom.parseString(data)
    contributors = root.getElementsByTagName('Contributor')
    conlist = []
    for contributor in contributors:
        conlist.append(contributor.firstChild.data)
    root.unlink()
    return conlist


def stringify(waveform):
    """Turn waveform object into NSCL-style station code

    :param waveform:
      Obspy Catalog Waveform object.
    :returns:
      NSCL- style string representation of waveform object.
    """
    fmt = '%s.%s.%s.%s'
    network = '--'
    if waveform.network_code is not None:
        network = waveform.network_code
    station = '--'
    if waveform.station_code is not None:
        station = waveform.station_code
    channel = '--'
    if waveform.channel_code is not None:
        channel = waveform.channel_code
    location = '--'
    if waveform.location_code is not None:
        location = waveform.location_code
    tpl = (network, station, channel, location)
    return fmt % tpl


def get_arrival(event, pickid):
    """Find the arrival object in a Catalog Event corresponding to input pick id.
    :param event:
      Obspy Catalog Event object.
    :param pickid:
      Pick ID string.
    :returns:
      Obspy Catalog arrival object.
    """
    for origin in event.origins:
        idlist = [arr.pick_id for arr in origin.arrivals]
        if pickid not in idlist:
            continue
        idx = idlist.index(pickid)
        arrival = origin.arrivals[idx]
        return arrival
    if pickid is None:
        return None


def _get_phaserow(pick, catevent):
    """Return a dictionary containing Phase data matching that found on ComCat event page.
    Example: https://earthquake.usgs.gov/earthquakes/eventpage/us2000ahv0#origin 
    (Click on the Phases tab).

    :param pick:
      Obspy Catalog Pick object.
    :param catevent:
      Obspy Catalog Event object.
    :returns:
      Dictionary containing:
        - Channel: NSCL-style channel string.
        - Distance: Distance (km) from station to origin.
        - Azimuth: Azimuth (deg.) from epicenter to station.
        - Phase: Name of the phase (Pn,Pg, etc.)
        - Arrival Time: Pick arrival time (UTC).
        - Status: "manual" or "automatic".
        - Residual: Arrival time residual.
        - Weight: Arrival weight.
    """
    pick_id = pick.resource_id
    waveform_id = pick.waveform_id
    arrival = get_arrival(catevent, pick_id)
    if arrival is None:
        #print('could not find arrival for pick %s' % pick_id)
        return None

    # save info to row of dataframe
    etime = pick.time.datetime
    channel = stringify(waveform_id)
    row = {'Channel': channel,
           'Distance': arrival.distance,
           'Azimuth': arrival.azimuth,
           'Phase': arrival.phase,
           'Arrival Time': etime,
           'Status': pick.evaluation_mode,
           'Residual': arrival.time_residual,
           'Weight': arrival.time_weight}
    return row


def get_phase_dataframe(detail, catalog='preferred'):
    """Return a Pandas DataFrame consisting of Phase arrival data.

    :param detail:
      DetailEvent object.
    :param catalog:
      Source network ('us','ak', etc. ,or 'preferred'.)
    :returns:
      Pandas DataFrame containing columns:
        - Channel: Network.Station.Channel.Location (NSCL) style station description.
                   ("--" indicates missing information)
        - Distance: Distance (kilometers) from epicenter to station.
        - Azimuth: Azimuth (degrees) from epicenter to station.
        - Phase: Name of the phase (Pn,Pg, etc.)
        - Arrival Time: Pick arrival time (UTC).
        - Status: "manual" or "automatic".
        - Residual: Arrival time residual.
        - Weight: Arrival weight.
    :raises:
      AttributeError if input DetailEvent does not have a phase-data product for the input catalog.
    """
    if catalog is None:
        catalog = 'preferred'
    df = pd.DataFrame(columns=['Channel', 'Distance', 'Azimuth',
                               'Phase', 'Arrival Time', 'Status',
                               'Residual', 'Weight'])

    phasedata = detail.getProducts('phase-data', source=catalog)[0]
    quakeurl = phasedata.getContentURL('quakeml.xml')
    try:
        fh = urlopen(quakeurl, timeout=TIMEOUT)
        data = fh.read()
        fh.close()
    except Exception as msg:
        return None
    unpickler = Unpickler()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        catalog = unpickler.loads(data)
        catevent = catalog.events[0]
        for pick in catevent.picks:
            phaserow = _get_phaserow(pick, catevent)
            if phaserow is None:
                continue
            df = df.append(phaserow, ignore_index=True)
    return df


def get_detail_data_frame(events, get_all_magnitudes=False,
                          get_tensors='preferred',
                          get_focals='preferred',
                          get_moment_supplement=False,
                          verbose=False):
    """Take the results of a search and extract the detailed event informat in a pandas DataFrame.

    Usage:
      TODO

    :param events:
      List of SummaryEvent objects as returned by search() function.
    :param get_all_magnitudes:
      Boolean indicating whether to return all magnitudes in results for each event.
    :param get_tensors:
      String option of 'none', 'preferred', or 'all'.
    :param get_focals:
      String option of 'none', 'preferred', or 'all'.
    :param get_moment_supplement:
      Boolean indicating whether derived origin and double-couple/source time information
      should be extracted (when available.)
    :returns:  
      Pandas DataFrame with one row per event, and all relevant information in columns.
    """
    elist = []
    ic = 0
    inc = min(100, np.power(10, np.floor(np.log10(len(events))) - 1))
    if verbose:
        sys.stderr.write(
            'Getting detailed event info - reporting every %i events.\n' % inc)
    for event in events:
        try:
            detail = event.getDetailEvent()
        except Exception as e:
            print('Failed to get detailed version of event %s' % event.id)
            continue
        edict = detail.toDict(get_all_magnitudes=get_all_magnitudes,
                              get_tensors=get_tensors,
                              get_moment_supplement=get_moment_supplement,
                              get_focals=get_focals)
        elist.append(edict)
        if ic % inc == 0 and verbose:
            msg = 'Getting detailed information for %s, %i of %i events.\n'
            sys.stderr.write(msg % (event.id, ic, len(events)))
        ic += 1
    df = pd.DataFrame(elist)
    first_columns = ['id', 'time', 'latitude',
                     'longitude', 'depth', 'magnitude']
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
    elist = []
    for event in events:
        elist.append(event.toDict())
    df = pd.DataFrame(elist)
    return df
