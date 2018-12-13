# stdlib imports
from xml.dom import minidom
import sys
from urllib.request import urlopen
import warnings
from datetime import datetime
import os.path
import json

# third party imports
import numpy as np
import pandas as pd
from obspy.io.quakeml.core import Unpickler
from libcomcat.classes import VersionOption
from obspy.clients.fdsn import Client
from impactutils.time.ancient_time import HistoricTime
from openpyxl import load_workbook
import requests

# local imports
from .classes import VersionOption

# constants
CATALOG_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/catalogs'
CONTRIBUTORS_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/contributors'
TIMEOUT = 60
TIMEFMT1 = '%Y-%m-%dT%H:%M:%S'
TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'
DATEFMT = '%Y-%m-%d'
COUNTRYFILE = 'ne_10m_admin_0_countries.shp'

# where is the PAGER fatality model found?
FATALITY_URL = 'https://raw.githubusercontent.com/usgs/pager/master/losspager/data/fatality.xml'
ECONOMIC_URL = 'https://raw.githubusercontent.com/usgs/pager/master/losspager/data/economy.xml'


def get_mag_src(mag):
    """Try to find the best magnitude source from a Magnitude object.

    Note: This can be difficult, as there is a great deal of variance
    in how magnitude information is submitted in QuakeML within ComCat.

    Args:
        mag (obspy Magnitude): Magnitude object from obspy.
    Returns:
        str: String indicating the most likely source of the
             magnitude solution.

    """
    c1 = mag.creation_info is not None
    if c1:
        c2 = mag.creation_info.agency_id is not None
    else:
        c2 = False
    if c2:
        magsrc = mag.creation_info.agency_id.lower()
    else:
        has_gcmt = mag.resource_id.id.lower().find('gcmt') > -1
        has_at = mag.resource_id.id.lower().find('at') > -1
        has_pt = mag.resource_id.id.lower().find('pt') > -1
        has_ak = (mag.resource_id.id.lower().find('ak') > -1 or
                  mag.resource_id.id.lower().find('alaska') > -1)
        has_pr = mag.resource_id.id.lower().find('pr') > -1
        has_dup = mag.resource_id.id.lower().find('duputel') > -1
        has_us = mag.resource_id.id.lower().find('us') > -1
        if has_gcmt:
            magsrc = 'gcmt'
        elif has_dup:
            magsrc = 'duputel'
        elif has_at:
            magsrc = 'at'
        elif has_pt:
            magsrc = 'pt'
        elif has_ak:
            magsrc = 'ak'
        elif has_pr:
            magsrc = 'pr'
        elif has_us:
            magsrc = 'us'
        else:
            magsrc = 'unknown'

    return magsrc


def get_all_mags(eventid):
    """Get all magnitudes for a given event ID.

    Args:
        eventid (str): ComCat Event ID.
    Returns:
        dict: Dictionary where keys are "magsrc-magtype" and values
              are magnitude value.

    """
    row = {}
    msg = ''
    client = Client('USGS')
    try:
        obsevent = client.get_events(eventid=eventid).events[0]
    except Exception as e:
        msg = 'Failed to download event %s, error "%s".' % (eventid, str(e))
    for mag in obsevent.magnitudes:
        magvalue = mag.mag
        magtype = mag.magnitude_type
        magsrc = get_mag_src(mag)
        colname = '%s-%s' % (magsrc, magtype)
        if colname in row:
            continue
        row[colname] = magvalue
    return (row, msg)



def read_phases(filename):
    """Read a phase file CSV or Excel file into data structures.

    Args:
        filename (str): String file name of a CSV or Excel file
            created by getphases program.
    Returns:
        tuple:
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

    Returns:
        list: Catalogs available in ComCat (see the catalog
            parameter in search() method.)
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

    Returns:
        list: Contributors available in ComCat (see the contributor
            parameter in search() method.)
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
