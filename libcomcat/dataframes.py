# stdlib imports
from xml.dom import minidom
import warnings
import json
from io import StringIO
from datetime import datetime, timedelta
import socket
import logging

# third party imports
import numpy as np
import pandas as pd
from obspy.io.quakeml.core import Unpickler
import requests
from scipy.special import erfcinv
from obspy.geodetics.base import gps2dist_azimuth
from impactutils.mapping.compass import get_compass_dir_azimuth

# local imports
from libcomcat.search import get_event_by_id, search
from libcomcat.exceptions import (ConnectionError, ParsingError,
                                  ProductNotFoundError,
                                  ProductNotSpecifiedError)
from libcomcat.utils import HEADERS, TIMEOUT

# constants
CATALOG_SEARCH_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/catalogs'
CONTRIBUTORS_SEARCH_TEMPLATE = ('https://earthquake.usgs.gov/fdsnws/event/1/'
                                'contributors')
TIMEFMT1 = '%Y-%m-%dT%H:%M:%S'
TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'
DATEFMT = '%Y-%m-%d'
COUNTRYFILE = 'ne_10m_admin_0_countries.shp'

# where is the PAGER fatality model found?
FATALITY_URL = ('https://raw.githubusercontent.com/usgs/pager/master/'
                'losspager/data/fatality.xml')
ECONOMIC_URL = ('https://raw.githubusercontent.com/usgs/pager/master/'
                'losspager/data/economy.xml')

# what are the DYFI columns and what do we rename them to?
DYFI_COLUMNS_REPLACE = {
    'Geocoded box': 'station',
    'CDI': 'intensity',
    'Latitude': 'lat',
    'Longitude': 'lon',
    'No. of responses': 'nresp',
    'Hypocentral distance': 'distance'
}

OLD_DYFI_COLUMNS_REPLACE = {
    'ZIP/Location': 'station',
    'CDI': 'intensity',
    'Latitude': 'lat',
    'Longitude': 'lon',
    'No. of responses': 'nresp',
    'Hypocentral distance': 'distance'
}

PRODUCT_COLUMNS = ['Update Time', 'Product', 'Authoritative Event ID', 'Code',
                   'Associated',
                   'Product Source', 'Product Version',
                   'Elapsed (min)', 'URL', 'Comment', 'Description']

SECSPERDAY = 86400
TIMEFMT = '%Y-%m-%d %H:%M:%S'
TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%fZ'
TIMEFMT3 = '%Y-%m-%d %H:%M:%S.%f'

PRODUCTS = ['dyfi', 'finite-fault',
            'focal-mechanism', 'ground-failure',
            'losspager', 'moment-tensor',
            'oaf', 'origin', 'phase-data',
            'shakemap']


def get_phase_dataframe(detail, catalog='preferred'):
    """Return a Pandas DataFrame consisting of Phase arrival data.

    Args:
        detail (DetailEvent): DetailEvent object.
        catalog (str): Source network ('us','ak', etc. ,or 'preferred'.)

    Returns:
        DataFrame: Pandas DataFrame containing columns:
            - Channel: Network.Station.Channel.Location (NSCL) style station
                       description. ("--" indicates missing information)
            - Distance: Distance (kilometers) from epicenter to station.
            - Azimuth: Azimuth (degrees) from epicenter to station.
            - Phase: Name of the phase (Pn,Pg, etc.)
            - Arrival Time: Pick arrival time (UTC).
            - Status: "manual" or "automatic".
            - Residual: Arrival time residual.
            - Weight: Arrival weight.
            - Agency: Agency ID.
    Raises:
        AttributeError: If input DetailEvent does not have a phase-data product
            for the input catalog.
    """
    if catalog is None:
        catalog = 'preferred'
    df = pd.DataFrame(columns=['Channel', 'Distance', 'Azimuth',
                               'Phase', 'Arrival Time', 'Status',
                               'Residual', 'Weight', 'Agency'])

    phasedata = detail.getProducts('phase-data', source=catalog)[0]
    quakeurl = phasedata.getContentURL('quakeml.xml')
    try:
        response = requests.get(quakeurl, timeout=TIMEOUT, headers=HEADERS)
        data = response.text.encode('utf-8')
    except Exception:
        return None
    unpickler = Unpickler()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        try:
            catalog = unpickler.loads(data)
        except Exception as e:
            fmt = 'Could not parse QuakeML from %s due to error: %s'
            msg = fmt % (quakeurl, str(e))
            raise ParsingError(msg)
        catevent = catalog.events[0]
        for pick in catevent.picks:
            station = pick.waveform_id.station_code
            fmt = 'Getting pick %s for station%s...'
            logging.debug(fmt % (pick.time, station))
            phaserow = _get_phaserow(pick, catevent)
            if phaserow is None:
                continue
            df = df.append(phaserow, ignore_index=True)
    return df


def _get_phaserow(pick, catevent):
    """Return a dictionary containing Phase data matching ComCat event page.
    Example:
    https://earthquake.usgs.gov/earthquakes/eventpage/us2000ahv0#origin
    (Click on the Phases tab).

    Args:
        pick (Pick): Obspy Catalog Pick object.
        catevent (Event): Obspy Catalog Event object.

    Returns:
        dict: Containing fields:
            - Channel: NSCL-style channel string.
            - Distance: Distance (km) from station to origin.
            - Azimuth: Azimuth (deg.) from epicenter to station.
            - Phase: Name of the phase (Pn,Pg, etc.)
            - Arrival Time: Pick arrival time (UTC).
            - Status: "manual" or "automatic".
            - Residual: Arrival time residual.
            - Weight: Arrival weight.
            - Agency: Agency ID.
    """
    pick_id = pick.resource_id
    waveform_id = pick.waveform_id
    arrival = get_arrival(catevent, pick_id)
    if arrival is None:
        return None

    # save info to row of dataframe
    etime = pick.time.datetime
    channel = stringify(waveform_id)
    agency_id = ''
    if arrival.creation_info is not None:
        agency_id = arrival.creation_info.agency_id
    row = {'Channel': channel,
           'Distance': arrival.distance,
           'Azimuth': arrival.azimuth,
           'Phase': arrival.phase,
           'Arrival Time': etime,
           'Status': pick.evaluation_mode,
           'Residual': arrival.time_residual,
           'Weight': arrival.time_weight,
           'Agency': agency_id}
    return row


def stringify(waveform):
    """Turn waveform object into NSCL-style station code

    Args:
        waveform (Waveform): Obspy Catalog Waveform object.
    Returns:
        str: NSCL- style string representation of waveform object.
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

    Args:
        event (Event): Obspy Catalog Event object.
        pickid (str): Pick ID string.

    Returns:
      Arrival: Obspy Catalog arrival object.
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


def get_magnitude_data_frame(detail, catalog, magtype):
    """Return a Pandas DataFrame consisting of magnitude data.

    Args:
        detail (DetailEvent): DetailEvent object.
        catalog (str): Source catalog ('us','ak', etc. ,or 'preferred'.)
        magtype (str): Magnitude type (mb, ml, etc.)

    Returns:
        DataFrame: Pandas DataFrame containing columns:
            - Channel: Network.Station.Channel.Location (NSCL) style station
                       description. ("--" indicates missing information)
            - Type: Magnitude type.
            - Amplitude: Amplitude of seismic wave at each station (m).
            - Period: Period of seismic wave at each station (s).
            - Status: "manual" or "automatic".
            - Magnitude: Locally determined magnitude.
            - Weight: Magnitude weight.
    Raises:
        AttributeError if input DetailEvent does not have a phase-data product
            for the input catalog.
    """
    columns = columns = ['Channel', 'Type', 'Amplitude',
                         'Period', 'Status', 'Magnitude',
                         'Weight']
    df = pd.DataFrame(columns=columns)
    phasedata = detail.getProducts('phase-data', source=catalog)[0]
    quakeurl = phasedata.getContentURL('quakeml.xml')
    try:
        response = requests.get(quakeurl, timeout=TIMEOUT, headers=HEADERS)
        data = response.text.encode('utf-8')
    except Exception:
        return None
    fmt = '%s.%s.%s.%s'
    unpickler = Unpickler()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        try:
            catalog = unpickler.loads(data)
        except Exception as e:
            fmt = 'Could not parse QuakeML from %s due to error: %s'
            msg = fmt % (quakeurl, str(e))
            raise ParsingError(msg)
        catevent = catalog.events[0]  # match this to input catalog
        for magnitude in catevent.magnitudes:
            if magnitude.magnitude_type.lower() != magtype.lower():
                continue
            for contribution in magnitude.station_magnitude_contributions:
                row = {}
                smag = contribution.station_magnitude_id.get_referred_object()
                ampid = smag.amplitude_id
                amp = None
                if ampid is None:
                    waveid = smag.waveform_id
                    tpl = (waveid.network_code,
                           waveid.station_code,
                           '--',
                           '--')
                else:
                    amp = ampid.get_referred_object()
                    if amp is None:
                        waveid = smag.waveform_id
                        tpl = (waveid.network_code,
                               waveid.station_code,
                               '--',
                               '--')
                    else:
                        waveid = amp.waveform_id
                        tpl = (waveid.network_code,
                               waveid.station_code,
                               waveid.channel_code,
                               waveid.location_code)

                row['Channel'] = fmt % tpl
                row['Type'] = smag.station_magnitude_type
                if amp is not None:
                    row['Amplitude'] = amp.generic_amplitude
                    row['Period'] = amp.period
                    row['Status'] = amp.evaluation_mode
                else:
                    row['Amplitude'] = np.nan
                    row['Period'] = np.nan
                    row['Status'] = 'automatic'
                row['Magnitude'] = smag.mag
                row['Weight'] = contribution.weight
                df = df.append(row, ignore_index=True)
    df = df[columns]
    return df


def get_detail_data_frame(events, get_all_magnitudes=False,
                          get_tensors='preferred',
                          get_focals='preferred',
                          get_moment_supplement=False,
                          verbose=False):
    """Extract the detailed event informat into a pandas DataFrame.

    Usage:
      TODO

    Args:
        events (list): List of SummaryEvent objects as returned by search()
                       function.
        get_all_magnitudes (bool): Boolean indicating whether to return all
            magnitudes in results for each event.
        get_tensors (str): String option of 'none', 'preferred', or 'all'.
        get_focals (str): String option of 'none', 'preferred', or 'all'.
        get_moment_supplement (bool): Indicates whether derived origin and
            double-couple/source time information
            should be extracted (when available.)

    Returns:
        DataFrame: Pandas DataFrame with one row per event, and all
            relevant information in columns.
    """
    elist = []
    ic = 0
    inc = min(100, np.power(10, np.floor(np.log10(len(events))) - 1))
    fmt = 'Getting detailed event info - reporting every %i events.'
    logging.debug(fmt % inc)
    for event in events:
        try:
            detail = event.getDetailEvent()
        except Exception:
            logging.warning(
                'Failed to get detailed version of event %s' % event.id)
            continue
        edict = detail.toDict(get_all_magnitudes=get_all_magnitudes,
                              get_tensors=get_tensors,
                              get_moment_supplement=get_moment_supplement,
                              get_focals=get_focals)
        elist.append(edict)
        if ic % inc == 0 and verbose:
            msg = 'Getting detailed information for %s, %i of %i events.\n'
            logging.debug(msg % (event.id, ic, len(events)))
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
    """Extract the summary event information from search results into DataFrame.

    Usage:
      TODO

    Args:
        events (list): List of SummaryEvent objects as returned by search()
            function.

    Returns:
        DataFrame: Pandas DataFrame with one row per event, and columns:
           - id (string) Authoritative ComCat event ID.
           - time (datetime) Authoritative event origin time.
           - latitude (float) Authoritative event latitude.
           - longitude (float) Authoritative event longitude.
           - depth (float) Authoritative event depth.
           - magnitude (float) Authoritative event magnitude.
           - significance (float) Event significance (600+ is ANSS significant)
    """
    elist = []
    for event in events:
        elist.append(event.toDict())
    df = pd.DataFrame(elist)
    return df


def get_pager_data_frame(detail, get_losses=False,
                         get_country_exposures=False,
                         get_all_versions=False):
    """Extract PAGER results for an event as a DataFrame.

    Args:
        detail (DetailEvent): Detailed information for a given event.
        get_losses (bool): Indicates whether to retrieve predicted fatalities
            and dollar losses and uncertainties.
        get_country_exposures (bool): Indicates whether to retrieve per-country
            shaking exposures.
        get_all_versions (bool): Indicates whether to retrieve PAGER results
                                 for all versions.
    Returns:
        (DataFrame): DataFrame whose columns will vary depending on input:
            (all):
            id - ComCat Event ID
            location - Location string for event.
            time - Date/time of event.
            latitude - Event latitude (dd)
            longitude - Event longitude (dd)
            depth - Event depth (km)
            magnitude - Event magnitude.
            mmi1 - Estimated population exposed to shaking at MMI intensity 1.
            ...
            mmi10 - Estimated population exposed to shaking at MMI intensity
                    10.
    """
    default_columns = ['id', 'location', 'time',
                       'latitude', 'longitude',
                       'depth', 'magnitude', 'country',
                       'pager_version',
                       'mmi1', 'mmi2',
                       'mmi3', 'mmi4',
                       'mmi5', 'mmi6',
                       'mmi7', 'mmi8',
                       'mmi9', 'mmi10']

    if not detail.hasProduct('losspager'):
        return None

    df = None
    for pager in detail.getProducts('losspager', version='all'):
        total_row = {}
        default = {}
        default['id'] = detail.id
        default['location'] = detail.location
        lat = detail.latitude
        lon = detail.longitude
        default['time'] = detail.time
        default['latitude'] = lat
        default['longitude'] = lon
        default['depth'] = detail.depth
        default['magnitude'] = detail.magnitude
        default['pager_version'] = pager.version
        total_row.update(default)
        total_row['country'] = 'Total'

        if len(pager.getContentsMatching('exposures.json')):
            total_row, country_rows = _get_json_exposure(total_row,
                                                         pager,
                                                         get_country_exposures,
                                                         default)

            if get_losses:
                loss_json = pager.getContentBytes(
                    'losses.json')[0].decode('utf-8')
                jdict = json.loads(loss_json)
                empfat = jdict['empirical_fatality']

                # get the list of country codes
                ccodes = [cfat['country_code']
                          for cfat in empfat['country_fatalities']]
                gfat, geco = get_g_values(ccodes)

                # get the total fatalities
                total_row['predicted_fatalities'] = empfat['total_fatalities']

                gfat_total, geco_total = _get_total_g(pager)
                # get the Gs/sigmas for total fatality
                fat_sigma = get_sigma(empfat['total_fatalities'], gfat_total)
                total_row['fatality_sigma'] = fat_sigma

                # get the total economic losses
                emploss = jdict['empirical_economic']
                total_row['predicted_dollars'] = emploss['total_dollars']

                # get the Gs/sigmas for total dollars
                eco_sigma = get_sigma(emploss['total_dollars'], geco_total)
                total_row['dollars_sigma'] = eco_sigma

                if get_country_exposures:
                    for country_fat in empfat['country_fatalities']:
                        fat = country_fat['fatalities']
                        ccode = country_fat['country_code']
                        # in at least one case (not sure why) PAGER results
                        # have fatalities per country but not exposures.
                        if ccode not in country_rows:
                            country_rows[ccode] = {}
                            country_rows[ccode].update(default)
                            country_rows[ccode]['country'] = ccode
                            country_rows[ccode]['mmi1'] = np.nan
                            country_rows[ccode]['mmi2'] = np.nan
                            country_rows[ccode]['mmi3'] = np.nan
                            country_rows[ccode]['mmi4'] = np.nan
                            country_rows[ccode]['mmi5'] = np.nan
                            country_rows[ccode]['mmi6'] = np.nan
                            country_rows[ccode]['mmi7'] = np.nan
                            country_rows[ccode]['mmi8'] = np.nan
                            country_rows[ccode]['mmi9'] = np.nan
                            country_rows[ccode]['mmi10'] = np.nan

                        country_rows[ccode]['predicted_fatalities'] = fat
                        if ccode in gfat:
                            gvalue = gfat[ccode]
                        else:
                            gvalue = np.nan
                        country_rows[ccode]['fatality_sigma'] = get_sigma(
                            fat, gvalue)

                    for country_eco in emploss['country_dollars']:
                        eco = country_eco['us_dollars']
                        ccode = country_eco['country_code']
                        country_rows[ccode]['predicted_dollars'] = eco
                        if ccode in geco:
                            gvalue = geco[ccode]
                        else:
                            gvalue = np.nan
                        country_rows[ccode]['dollars_sigma'] = get_sigma(
                            eco, gvalue)

        else:  # event does not have JSON content
            country_rows = {}
            total_row = _get_xml_exposure(total_row, pager, get_losses)

        columns = default_columns
        if get_losses:
            columns = default_columns + ['predicted_fatalities',
                                         'fatality_sigma',
                                         'predicted_dollars',
                                         'dollars_sigma']
        if df is None:
            df = pd.DataFrame(columns=columns)
        df = df.append(total_row, ignore_index=True)
        for ccode, country_row in country_rows.items():
            df = df.append(country_row, ignore_index=True)

    df = df[columns]
    # countries with zero fatalities don't report, so fill in with zeros
    if get_losses:
        df['predicted_fatalities'] = df['predicted_fatalities'].fillna(value=0)
        df['fatality_sigma'] = df['fatality_sigma'].fillna(value=0)
        df['predicted_dollars'] = df['predicted_dollars'].fillna(value=0)
        df['dollars_sigma'] = df['dollars_sigma'].fillna(value=0)

    return df


def _invphi(input):
    """Inverse phi function.

    Args:
    input (float or ndarray): Float (scalar or array) value.
    Returns:
      float: invphi(input)
    """
    return -1 * np.sqrt(2) * erfcinv(input / 0.5)


def _get_total_g(pager):
    """Retrieve the G norm value for the aggregated losses.

    Args:
        pager (Product): PAGER ComCat Product.
    Returns:
        tuple: (Aggregated Fatality G value, Aggregated Economic G value)
    """
    alert_json = pager.getContentBytes(
        'alerts.json')[0].decode('utf-8')
    jdict = json.loads(alert_json)
    gfat = jdict['fatality']['gvalue']
    geco = jdict['economic']['gvalue']
    return (gfat, geco)


def _get_xml_exposure(total_row, pager, get_losses):
    """Retrieve aggregated exposure from events prior to new PAGER release.

    Args:
        total_row (dict): Dictionary to be filled in with exposures.
        pager (Product): PAGER ComCat Product.
        get_losses (bool): If losses are desired, fill in values with NaN.
    Returns:
        dict: Filled in total_row.
    """
    if not len(pager.getContentsMatching('pager.xml')):
        for i in range(0, 11):
            mmistr = 'mmi%i' % i
            total_row[mmistr] = np.nan
        total_row['predicted_fatalities'] = np.nan
        total_row['predicted_dollars'] = np.nan
    else:
        xmlbytes, xmlurl = pager.getContentBytes('pager.xml')
        exposure_xml = xmlbytes.decode('utf-8')
        root = minidom.parseString(exposure_xml)
        pager = root.getElementsByTagName('pager')[0]
        if get_losses:
            total_row['predicted_fatalities'] = np.nan
            total_row['predicted_dollars'] = np.nan
        for node in pager.childNodes:
            if node.localName != 'exposure':
                continue
            mmistr = 'mmi%i' % (int(float(node.getAttribute('dmax'))))
            total_row[mmistr] = int(node.getAttribute('exposure'))
            total_row['ccode'] = 'Total'
        root.unlink()
    return total_row


def _get_json_exposure(total_row, pager, get_country_exposures, default):
    """Retrieve aggregated/country exposures from events after new PAGER release.

    Args:
        total_row (dict): Dictionary to be filled in with exposures.
        pager (Product): PAGER ComCat Product.
        get_country_exposures (bool): Extract exposures for each affected
                                      country.
    Returns:
        tuple: (total_row, country_rows)
    """
    exposure_json = pager.getContentBytes('exposures.json')[0].decode('utf-8')
    jdict = json.loads(exposure_json)
    exp = jdict['population_exposure']['aggregated_exposure']
    total_row['mmi1'] = exp[0]
    total_row['mmi2'] = exp[1]
    total_row['mmi3'] = exp[2]
    total_row['mmi4'] = exp[3]
    total_row['mmi5'] = exp[4]
    total_row['mmi6'] = exp[5]
    total_row['mmi7'] = exp[6]
    total_row['mmi8'] = exp[7]
    total_row['mmi9'] = exp[8]
    total_row['mmi10'] = exp[9]
    country_rows = {}
    if get_country_exposures:
        for country in jdict['population_exposure']['country_exposures']:
            country_row = {}
            ccode = country['country_code']
            country_row.update(default)
            country_row['country'] = ccode
            exp = country['exposure']
            country_row['mmi1'] = exp[0]
            country_row['mmi2'] = exp[1]
            country_row['mmi3'] = exp[2]
            country_row['mmi4'] = exp[3]
            country_row['mmi5'] = exp[4]
            country_row['mmi6'] = exp[5]
            country_row['mmi7'] = exp[6]
            country_row['mmi8'] = exp[7]
            country_row['mmi9'] = exp[8]
            country_row['mmi10'] = exp[9]
            country_rows[ccode] = country_row

    return (total_row, country_rows)


def get_sigma(loss, gvalue):
    """Calculate sigma value for a given loss value and G statistic.

    Args:
        loss (float): Fatality or economic loss value.
        gvalue (float): G statistic for model.
    Returns:
        float: One sigma value.
    """
    if loss == 0:
        loss = 0.5
    percent = 0.6827
    prob = round(np.exp(gvalue * _invphi(percent) + np.log(loss)))
    return prob


def get_g_values(ccodes):
    """Retrieve G values for given country codes from PAGER repository.

    Args:
        ccodes (list): Sequence of two-letter country codes.
    Returns:
        tuple: (Dictionary of fatality G values, Dictionary of economic G
                values)

    """
    res = requests.get(FATALITY_URL, timeout=TIMEOUT, headers=HEADERS)
    root = minidom.parseString(res.text)
    res.close()
    models = root.getElementsByTagName(
        'models')[0].getElementsByTagName('model')
    fatmodels = {}
    for model in models:
        ccode = model.getAttribute('ccode')
        if ccode in ccodes:
            fatmodels[ccode] = float(model.getAttribute('evalnormvalue'))
    root.unlink()

    response = requests.get(ECONOMIC_URL)
    root = minidom.parseString(response.text)
    models = root.getElementsByTagName(
        'models')[0].getElementsByTagName('model')
    ecomodels = {}
    for model in models:
        ccode = model.getAttribute('ccode')
        if ccode in ccodes:
            ecomodels[ccode] = float(model.getAttribute('evalnormvalue'))
    root.unlink()

    return (fatmodels, ecomodels)


def get_dyfi_data_frame(detail, dyfi_file=None,
                        version='preferred'):
    """Retrieve a pandas DataFrame containing DYFI responses.

    Args:
        detail (DetailEvent): DetailEvent object.
        dyfi_file (str or None): If None, the file is chosen from the
                                 following list, in the order presented.
                                - utm_1km: UTM aggregated at 1km resolution.
                                - utm_10km: UTM aggregated at 10km resolution.
                                - utm_var: UTM aggregated "best" resolution
                                           for map.
                                - zip: ZIP/city aggregated.
        version (str): DYFI version ('first','last','preferred','all').

    Returns:
        DataFrame or None: Pandas DataFrame containing columns:
            - station: Name of the location where aggregated responses are
                       located.
            - lat: Latitude of responses.
            - lon: Longitude of responses.
            - distance: Distance from epicenter to location of aggregated
                        responses.
            - intensity: Modified Mercalli Intensity
            - nresp: Number of DYFI responses at aggregated location.

    This function returns None if no DYFI products were found.
    """
    if not detail.hasProduct('dyfi'):
        return None
    dyfi = detail.getProducts('dyfi', version=version)[0]
    files = ['dyfi_geo_1km.geojson',
             'dyfi_geo_10km.geojson',
             'cdi_geo.txt',
             'cdi_zip.txt']
    dataframe = None
    if dyfi_file is not None:
        if dyfi_file == 'utm_1km':
            if 'dyfi_geo_1km.geojson' not in dyfi.contents:
                return None
            data, _ = dyfi.getContentBytes('dyfi_geo_1km.geojson')
            dataframe = _parse_geojson(data)
        elif dyfi_file == 'utm_10km':
            if 'dyfi_geo_10km.geojson' not in dyfi.contents:
                return None
            data, _ = dyfi.getContentBytes('dyfi_geo_10km.geojson')
            dataframe = _parse_geojson(data)
        elif dyfi_file == 'utm_var':
            if 'cdi_geo.txt' not in dyfi.contents:
                return None
            data, _ = dyfi.getContentBytes('cdi_geo.txt')
            dataframe = _parse_text(data)
        elif dyfi_file == 'zip':
            if 'cdi_zip.txt' not in dyfi.contents:
                return None
            data, _ = dyfi.getContentBytes('cdi_zip.txt')
            dataframe = _parse_text(data)
    else:
        for file in files:
            if file in dyfi.contents:
                data, _ = dyfi.getContentBytes(file)
                if file.endswith('geojson'):
                    dataframe = _parse_geojson(data)
                else:
                    dataframe = _parse_text(data)
                break
    columns = ['station', 'lat', 'lon', 'distance', 'intensity', 'nresp']
    dataframe = dataframe[columns]
    return dataframe


def _parse_text(bytes_geo):
    text_geo = bytes_geo.decode('utf-8')
    lines = text_geo.split('\n')
    columns = lines[0].split(':')[1].split(',')
    columns = [col.strip() for col in columns]
    columns = [col.strip('[') for col in columns]
    columns = [col.strip(']') for col in columns]
    fileio = StringIO(text_geo)
    df = pd.read_csv(fileio, skiprows=1, names=columns)
    if 'ZIP/Location' in columns:
        df = df.rename(index=str, columns=OLD_DYFI_COLUMNS_REPLACE)
    else:
        df = df.rename(index=str, columns=DYFI_COLUMNS_REPLACE)
    df = df.drop(['Suspect?', 'City', 'State'], axis=1)
    # df = df[df['nresp'] >= MIN_RESPONSES]
    return df


def _parse_geojson(bytes_data):
    text_data = bytes_data.decode('utf-8')
    jdict = json.loads(text_data)
    if len(jdict['features']) == 0:
        return None
    prop_columns = list(jdict['features'][0]['properties'].keys())
    columns = ['lat', 'lon'] + prop_columns
    arrays = [[] for col in columns]
    df_dict = dict(zip(columns, arrays))
    for feature in jdict['features']:
        for column in prop_columns:
            if column == 'name':
                prop = feature['properties'][column]
                prop = prop[0: prop.find('<br>')]
            else:
                prop = feature['properties'][column]

            df_dict[column].append(prop)
        # the geojson defines a box, so let's grab the center point
        lons = [c[0] for c in feature['geometry']['coordinates'][0]]
        lats = [c[1] for c in feature['geometry']['coordinates'][0]]
        clon = np.mean(lons)
        clat = np.mean(lats)
        df_dict['lat'].append(clat)
        df_dict['lon'].append(clon)

    df = pd.DataFrame(df_dict)
    df = df.rename(index=str, columns={
        'cdi': 'intensity',
        'dist': 'distance',
        'name': 'station'
    })
    return df


def get_history_data_frame(detail, products=None):
    """Retrieve an event history information table given a ComCat Event ID.

    Args:
        detail (DetailEvent): DetailEvent object.
        products (list): List of ComCat products to retrieve, or None
                         retrieves all.
    Returns:
        tuple:
            - pandas DataFrame containing columns:
                - Product:
                    One of supported products (see
                    libcomcat.dataframes.PRODUCTS)
                - Authoritative Event ID:
                    Authoritative ComCat event ID.
                - Code:
                    Event Source + Code, mostly only useful when using
                    -r flag with geteventhist.
                - Associated:
                    Boolean indicating whether this product is associated
                    with authoritative event.
                - Product Source:
                    Network that contributed the product.
                - Product Version:
                    Either ordinal number created by sorting products from a
                    given source, or a version property set by the creator
                    of the product.
                - Update Time:
                    Time the product was sent, set either by PDL client or
                    by the person or software that created the product
                    (set as a property.)
                - Elapsed (min):
                    Elapsed time in minutes between the update time and
                    the *authoritative* origin time.
                - URL:
                    The most representative URL for that *version* of the
                    given product.
                - Description:
                    Varies depending on the product, but all description
                    fields are delineated first by a vertical pipe "|",
                    and key/value pairs in each field are delineated
                    by a hash "#". This is so that the split_history_frame()
                    function can parse the description column into many
                    columns.
            - DetailEvent: libcomcat DetailEvent object.
    """
    event = detail
    if products is not None:
        if not len(set(products) & set(PRODUCTS)):
            fmt = '''None of the input products "%s" are in the list
            of supported ComCat products: %s.
            '''
            tpl = (','.join(products), ','.join(PRODUCTS))
            raise ProductNotFoundError(fmt % tpl)
    else:
        products = PRODUCTS

    dataframe = pd.DataFrame(columns=PRODUCT_COLUMNS)
    for product in products:
        logging.debug('Searching for %s products...' % product)
        if not event.hasProduct(product):
            continue
        prows = _get_product_rows(event, product)
        dataframe = dataframe.append(prows, ignore_index=True)

    dataframe = dataframe.sort_values('Update Time')
    dataframe['Elapsed (min)'] = np.round(dataframe['Elapsed (min)'], 1)
    dataframe['Comment'] = ''
    dataframe = dataframe[PRODUCT_COLUMNS]
    return (dataframe, event)


def _get_product_rows(event, product_name):
    products = event.getProducts(product_name,
                                 source='all',
                                 version='all')
    prows = pd.DataFrame(columns=PRODUCT_COLUMNS)
    for product in products:
        # if product.contents == ['']:
        #     continue
        if product.name == 'origin':
            prow = _describe_origin(event, product)
        elif product.name == 'shakemap':
            prow = _describe_shakemap(event, product)
        elif product.name == 'dyfi':
            prow = _describe_dyfi(event, product)
        elif product.name == 'losspager':
            prow = _describe_pager(event, product)
        elif product.name == 'oaf':
            prow = _describe_oaf(event, product)
        elif product.name == 'finite-fault':
            prow = _describe_finite_fault(event, product)
        elif product.name == 'focal-mechanism':
            prow = _describe_focal_mechanism(event, product)
        elif product.name == 'ground-failure':
            prow = _describe_ground_failure(event, product)
        elif product.name == 'moment-tensor':
            prow = _describe_moment_tensor(event, product)
        elif product.name == 'phase-data':
            prow = _describe_origin(event, product)
        else:
            continue
        prows = prows.append(prow, ignore_index=True)

    return prows


def _describe_pager(event, product):
    authtime = event.time

    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    oid = product['eventsource'] + product['eventsourcecode']
    productsource = 'us'

    # get pager version, alert level, and max exposure from JSON
    # or xml files.
    pversion = 0
    alertlevel = ''
    max_exp = 0
    maxmmi = 0
    if product.hasProperty('maxmmi'):
        maxmmi = int(float(product['maxmmi']))

        has_json = len(product.getContentsMatching('event.json')) == 1
        has_xml = len(product.getContentsMatching('pager.xml'))
        if has_json:
            eventinfo_bytes = product.getContentBytes('event.json')[0]
            eventinfo = json.loads(eventinfo_bytes.decode('utf-8'))
            pversion = eventinfo['pager']['version_number']
            alertlevel = eventinfo['pager']['true_alert_level']

            exp_bytes = product.getContentBytes('exposures.json')[0]
            expinfo = json.loads(exp_bytes.decode('utf-8'))
            expdict = expinfo['population_exposure']
            max_exp = expdict['aggregated_exposure'][maxmmi - 1]
        elif has_xml:
            xmlbytes = product.getContentBytes('pager.xml')[0]
            root = minidom.parseString(xmlbytes.decode('utf-8'))
            eventobj = root.getElementsByTagName('event')[0]
            pversion = int(eventobj.getAttribute('number'))
            alerts = root.getElementsByTagName('alert')
            for alert in alerts:
                if alert.getAttribute('summary') == 'no':
                    continue
                alertlevel = alert.getAttribute('level')

            exposures = []
            for exposure in root.getElementsByTagName('exposure'):
                try:
                    expval = int(float(exposure.getAttribute('exposure')))
                except ValueError:
                    expval = 0
                exposures.append(expval)
            exposures = np.array(exposures)
            max_exp = exposures[maxmmi - 1]
            root.unlink()

    fmt = 'AlertLevel# %s| MaxMMI# %i|Population@MaxMMI# %i'
    tpl = (alertlevel.capitalize(), maxmmi, max_exp)
    desc = fmt % tpl
    url = product.getContentURL('onepager.pdf')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_shakemap(event, product):
    authtime = event.time
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60

    oid = 'unknown'
    productsource = 'unknown'
    if product.hasProperty('eventsource'):
        oid = product['eventsource'] + product['eventsourcecode']
        productsource = product.source

    # get from info:
    # - fault file or reference
    # - gmpe
    # - magnitude used
    # - magnitude type used ?
    # - depth used
    maxmmi = 0
    ninstrument = 0
    ndyfi = 0
    fault_ref = ''
    gmpe = ''
    mag_used = np.nan
    depth_used = np.nan
    pversion = 0
    if product.hasProperty('maxmmi'):
        maxmmi = float(product['maxmmi'])
        pversion = int(product['version'])

        (ninstrument, ndyfi, mag_used,
         depth_used, fault_file, gmpe) = _get_shakemap_info(product)

    fmt = ('MaxMMI# %.1f|Instrumented# %i|DYFI# %i|Fault# %s|'
           'GMPE# %s|Mag# %.1f|Depth# %.1f')
    tpl = (maxmmi, ninstrument, ndyfi, fault_ref, gmpe, mag_used, depth_used)
    desc = fmt % tpl
    url = product.getContentURL('intensity.jpg')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _get_shakemap_info(product):
    if len(product.getContentsMatching('info.json')):
        infobytes = product.getContentBytes('info.json')[0]
        infodict = json.loads(infobytes.decode('utf-8'))
        try:
            gmpe = ','.join(infodict['multigmpe']['PGA']['gmpes'][0]['gmpes'])
        except Exception:
            gmpedict = infodict['processing']['ground_motion_modules']
            gmpe = gmpedict['gmpe']['module']

        gmpe = gmpe.replace('()', '')

        fault_ref = infodict['input']['event_information']['fault_ref']
        fault_file = ''
        if 'faultfiles' in infodict['input']['event_information']:
            fault_file = infodict['input']['event_information']['faultfiles']
        if not len(fault_ref) and len(fault_file):
            fault_ref = fault_file
        mag_used = float(infodict['input']['event_information']['magnitude'])
        depth_used = float(infodict['input']['event_information']['depth'])

        # get from stations
        # - number instrumented stations
        # - number dyfi
        stationbytes = product.getContentBytes('stationlist.json')[0]
        stationdict = json.loads(stationbytes.decode('utf-8'))
        ninstrument = 0
        ndyfi = 0
        for feature in stationdict['features']:
            if feature['properties']['source'] == 'DYFI':
                ndyfi += 1
            else:
                ninstrument += 1
    elif len(product.getContentsMatching('info.xml')):
        infobytes = product.getContentBytes('info.xml')[0]
        root = minidom.parseString(infobytes.decode('utf-8'))
        fault_ref = ''
        fault_file = ''
        gmpe = ''
        for tag in root.getElementsByTagName('tag'):
            ttype = tag.getAttribute('name')
            if ttype == 'GMPE':
                gmpe = tag.getAttribute('value')
            elif ttype == 'fault_ref':
                fault_ref = tag.getAttribute('value')
            elif ttype == 'fault_files':
                fault_file = tag.getAttribute('value')
            else:
                continue
        if len(fault_ref) and not len(fault_file):
            fault_file = fault_ref
        root.unlink()
        if len(product.getContentsMatching('stationlist.xml')):
            stationbytes = product.getContentBytes('stationlist.xml')[0]
            root = minidom.parseString(stationbytes.decode('utf-8'))
            ndyfi = 0
            ninstrument = 0
            for station in root.getElementsByTagName('station'):
                netid = station.getAttribute('netid')
                if netid.lower() in ['dyfi', 'ciim', 'intensity', 'mmi']:
                    ndyfi += 1
                else:
                    ninstrument += 1
            eq = root.getElementsByTagName('earthquake')[0]
            mag_used = float(eq.getAttribute('mag'))
            depth_used = float(eq.getAttribute('depth'))
            root.unlink()
    else:
        ninstrument = 0
        ndyfi = 0
        mag_used = np.nan
        depth_used = np.nan
        fault_file = ''
        gmpe = ''

    return (ninstrument, ndyfi, mag_used, depth_used, fault_file, gmpe)


def _describe_origin(event, product):
    authtime = event.time
    authlat = event.latitude
    authlon = event.longitude

    oid = 'unknown'
    productsource = product.source
    if product.hasProperty('eventsource'):
        oid = product['eventsource'] + product['eventsourcecode']
        productsource = product['eventsource']
    omag = np.nan
    if product.hasProperty('magnitude'):
        omag = float(product['magnitude'])

    magtype = 'unknown'
    if product.hasProperty('magnitude-type'):
        magtype = product['magnitude-type']

    otime = 'NaT'
    tdiff = np.nan
    if product.hasProperty('eventtime'):
        otime_str = product['eventtime']
        otime = datetime.strptime(otime_str, TIMEFMT2)
        tdiff = (otime - authtime).total_seconds()
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60

    olat = np.nan
    olon = np.nan
    odepth = np.nan
    dist = np.nan
    az = np.nan
    url = ''
    if len(product.getContentsMatching('quakeml.xml')):
        url = product.getContentURL('quakeml.xml')
    elif len(product.getContentsMatching('eqxml.xml')):
        url = product.getContentURL('eqxml.xml')
    if product.hasProperty('latitude'):
        olat = float(product['latitude'])
        olon = float(product['longitude'])
        odepth = float(product['depth'])
        dist_m, az, _ = gps2dist_azimuth(authlat, authlon, olat, olon)
        dist = dist_m / 1000.0
    else:
        if len(product.getContentsMatching('quakeml.xml')):
            unpickler = Unpickler()
            cbytes, url = product.getContentBytes('quakeml.xml')
            try:
                catalog = unpickler.loads(cbytes)
            except Exception as e:
                fmt = 'Could not parse QuakeML from %s due to error: %s'
                msg = fmt % (url, str(e))
                raise ParsingError(msg)
            evt = catalog.events[0]
            if hasattr(evt, 'origin'):
                origin = evt.origin
                olat = origin.latitude
                olon = origin.longitude
                odepth = origin.depth / 1000
                dist_m, az, _ = gps2dist_azimuth(authlat, authlon, olat, olon)
                dist = dist_m / 1000.0

    loc_method = 'unknown'
    if product.hasProperty('cube-location-method'):
        loc_method = product['cube-location-method']

    # convert azimuth to cardinal direction
    if not np.isnan(az):
        azstr = get_compass_dir_azimuth(az, resolution='meteorological')
    else:
        azstr = ''

    # get the origin weight - this should help us determine which
    # origin is authoritative
    weight = product.preferred_weight

    fmt = ('Magnitude# %.1f|Time# %s |Time Offset (sec)# %.1f|'
           'Location# (%.3f,%.3f)|Distance from Auth. Origin (km)# %.1f|'
           'Azimuth# %s|Depth# %.1f|Magnitude Type# %s|Location Method# %s|'
           'Preferred Weight#%i')
    desc = fmt % (omag, otime, tdiff,
                  olat, olon, dist, azstr,
                  odepth, magtype, loc_method,
                  weight)

    pversion = product.version
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_finite_fault(event, product):
    authtime = event.time
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    oid = product['eventsource'] + product['eventsourcecode']
    productsource = product.source

    slip = np.nan
    strike = np.nan
    dip = np.nan
    if product.hasProperty('maximum-slip'):
        slip = float(product['maximum-slip'])
        strike = float(product['segment-1-strike'])
        dip = float(product['segment-1-dip'])

    fmt = 'Peak Slip# %.3f|Strike# %.0f|Dip# %.0f'
    tpl = (slip, strike, dip)
    desc = fmt % tpl
    pversion = product.version
    url = product.getContentURL('basemap.png')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_dyfi(event, product):
    authtime = event.time
    maxmmi = np.nan
    if product.hasProperty('maxmmi'):
        maxmmi = float(product['maxmmi'])
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    oid = product['eventsource'] + product['eventsourcecode']
    nresp = 0
    if product.hasProperty('num-responses'):
        nresp = int(product['num-responses'])
    productsource = 'us'
    desc = 'Max MMI# %.1f|NumResponses# %i' % (maxmmi, nresp)
    pversion = product.version
    url = product.getContentURL('ciim_geo.jpg')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_focal_mechanism(event, product):
    authtime = event.time
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    oid = product['eventsource'] + product['eventsourcecode']
    productsource = product['eventsource']

    if product.hasProperty('nodal-plane-1-strike'):
        strike = float(product['nodal-plane-1-strike'])
        dip = float(product['nodal-plane-1-dip'])
        rake = float(product['nodal-plane-1-rake'])
    else:
        strike = np.nan
        dip = np.nan
        rake = np.nan

    method = 'unknown'
    if len(product.getContentsMatching('quakeml.xml')):
        cbytes, url = product.getContentBytes('quakeml.xml')
        unpickler = Unpickler()
        try:
            catalog = unpickler.loads(cbytes)
        except Exception as e:
            fmt = 'Could not parse QuakeML from %s due to error: %s'
            msg = fmt % (url, str(e))
            raise ParsingError(msg)
        evt = catalog.events[0]
        fm = evt.focal_mechanisms[0]
        if hasattr(fm, 'method_id') and hasattr(fm.method_id, 'id'):
            method = fm.method_id.id.split('/')[-1]

    fmt = 'Method# %s|NP1 Strike# %.1f|NP1 Dip# %.1f|NP1 Rake# %.1f'
    tpl = (method, strike, dip, rake)
    desc = fmt % tpl
    pversion = product.version
    if len(product.getContentsMatching('cifm1.jpg')):
        url = product.getContentURL('cifm1.jpg')
    else:
        url = product.getContentURL('quakeml.xml')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_ground_failure(event, product):
    authtime = event.time
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    if product.hasProperty('eventsource'):
        oid = product['eventsource'] + product['eventsourcecode']
    else:
        oid = 'unknown'
    productsource = 'us'

    slide_alert = product['landslide-alert']
    liq_alert = product['liquefaction-alert']
    slide_pop_alert_val = int(product['landslide-population-alert-value'])
    liq_pop_alert_val = int(product['liquefaction-population-alert-value'])

    # get the shakemap event ID and magnitude from info.json
    infobytes = product.getContentBytes('info.json')[0]
    infodict = json.loads(infobytes.decode('utf-8'))
    sm_net = infodict['Summary']['net']
    sm_code = infodict['Summary']['code']
    sm_eventid = sm_net + sm_code
    sm_mag = infodict['Summary']['magnitude']

    fmt = ('ShakeMap Event ID# %s|ShakeMap Magnitude# %.1f|'
           'Landslide Pop Alert Value# %i|Liquefaction Pop Alert Value# %i|'
           'Landslide Alert# %s|Liquefaction Alert# %s')
    tpl = (sm_eventid, sm_mag, slide_pop_alert_val,
           liq_pop_alert_val, slide_alert, liq_alert)
    desc = fmt % tpl
    pversion = int(product['version'])
    url = product.getContentURL('info.json')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_moment_tensor(event, product):
    authtime = event.time
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    oid = product['eventsource'] + product['eventsourcecode']
    productsource = product['eventsource']

    # try to find the method
    method = 'unknown'
    if product.hasProperty('derived-magnitude-type'):
        method = product['derived-magnitude-type']

    # get the derived moment magnitude
    derived_mag = np.nan
    if product.hasProperty('derived-magnitude'):
        derived_mag = float(product['derived-magnitude'])

    # get the derived depth
    derived_depth = np.nan
    if product.hasProperty('derived-depth'):
        derived_depth = float(product['derived-depth'])

    # get the percent double couple
    double_couple = np.nan
    if product.hasProperty('percent-double-couple'):
        double_couple = float(product['percent-double-couple'])

    strike = np.nan
    dip = np.nan
    rake = np.nan
    # get the first nodal plane
    if product.hasProperty('nodal-plane-1-strike'):
        strike = float(product['nodal-plane-1-strike'])
        dip = float(product['nodal-plane-1-dip'])
        rake = float(product['nodal-plane-1-rake'])
    else:
        # try to get NP1 from the quakeml...
        if len(product.getContentsMatching('quakeml.xml')):
            cbytes, url = product.getContentBytes('quakeml.xml')
            unpickler = Unpickler()
            try:
                catalog = unpickler.loads(cbytes)
            except Exception as e:
                fmt = 'Could not parse QuakeML from %s due to error: %s'
                msg = fmt % (url, str(e))
                raise ParsingError(msg)
            evt = catalog.events[0]
            fm = evt.focal_mechanisms[0]
            mt = fm.moment_tensor
            if method == 'unknown':
                method = mt.method_id.id.split('/')[-1]
            if fm.nodal_planes is not None:
                strike = fm.nodal_planes.nodal_plane_1.strike
                dip = fm.nodal_planes.nodal_plane_1.dip
                rake = fm.nodal_planes.nodal_plane_1.rake
            if np.isnan(derived_mag):
                derived_mag = evt.magnitudes[0].mag
            if np.isnan(derived_depth):
                for origin in evt.origins:
                    if 'moment' in origin.depth_type:
                        derived_depth = origin.depth / 1000
            if np.isnan(double_couple):
                double_couple = mt.double_couple

    desc_fmt = ('Method# %s|Moment Magnitude# %.1f|Depth# %.1d|'
                'Double Couple# %.2f|NP1 Strike# %.0f|NP1 Dip# %.0f|'
                'NP1 Rake# %.0f')
    desc_tpl = (method, derived_mag, derived_depth,
                double_couple, strike, dip, rake)
    desc = desc_fmt % desc_tpl
    pversion = product.version
    url = product.getContentURL('quakeml.xml')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def _describe_oaf(event, product):
    authtime = event.time
    ptime = datetime.utcfromtimestamp(product.product_timestamp / 1000)
    elapsed = ptime - authtime
    elapsed_sec = elapsed.days * SECSPERDAY + \
        elapsed.seconds + elapsed.microseconds / 1e6
    elapsed_min = elapsed_sec / 60
    oid = product['eventsource'] + product['eventsourcecode']
    productsource = product['eventsource']

    desc = 'Operational Earthquake Forecast# Info'
    pversion = product.version
    url = ''
    logging.info('%s version %i' % (product.name, product.version))
    if product.getContentsMatching('json'):
        url = product.getContentURL('forecast_data.json')
    row = {'Product': product.name,
           'Authoritative Event ID': event.id,
           'Code': oid,
           'Associated': True,
           'Product Source': productsource,
           'Product Version': pversion,
           'Update Time': ptime,
           'Elapsed (min)': elapsed_min,
           'URL': url,
           'Description': desc}
    return row


def split_history_frame(dataframe, product=None):
    """Split event history dataframe for a given product.

    The "Description" field will be parsed into separate columns.
    For example, an origin might have the following description:

    Magnitude# 4.4|Depth# 12.2|Time# 2019-07-16 20:11:01.510000 |\
    Time Offset (sec)# 0.0|Location# (37.816,-121.766)|\
    Distance from Auth. Origin (km)# 0.9|Magnitude Type# ml|\
    Location Method# unknown

    This would be split into 8 separate columns on the "|" character,
    and the column names and values will be taken by splitting each field
    on the "#" character.

    Args:
        dataframe (pandas.DataFrame):
            Result of calling get_history_data_frame.
        product (str):
            One of the products found in the Product column.
    Returns:
        pandas.DataFrame: DataFrame containing columns extracted from
            input Description column, and Description column removed.


    """
    products = dataframe['Product'].unique()
    if product is not None and product not in products:
        raise ProductNotFoundError(
            '%s is not a product found in this dataframe.' % product)
    if product is None and len(products) > 1:
        raise ProductNotSpecifiedError('Dataframe contains many products, '
                                       'you must specify one of them to '
                                       'split.')
    if product is not None:
        dataframe = dataframe[dataframe['Product'] == product]
    parts = dataframe.iloc[0]['Description'].split('|')
    columns = [p.split('#')[0] for p in parts]
    df2 = pd.DataFrame(columns=columns)
    for idx, row in dataframe.iterrows():
        parts = row['Description'].split('|')
        columns = [p.split('#')[0].strip() for p in parts]
        values = [p.split('#')[1].strip() for p in parts]
        newvalues = []
        for val in values:
            try:
                newval = float(val)
            except ValueError:
                try:
                    newval = pd.Timestamp(val)
                except ValueError:
                    newval = val
            newvalues.append(newval)
        ddict = dict(zip(columns, newvalues))
        row = pd.Series(ddict)
        df2 = df2.append(row, ignore_index=True)

    dataframe = dataframe.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    dataframe = pd.concat([dataframe, df2], axis=1)
    dataframe = dataframe.drop(['Description'], axis='columns')
    dataframe = dataframe.sort_values('Update Time')

    return dataframe


def find_nearby_events(time, lat, lon, twindow, radius):
    """Return dataframe containing events near (time/space) input event.

    Rows in the dataframe will be sorted in ascending order by the
    normalized_time_dist_vector column (see below), such that the first row in
    the dataframe is the best match according to that metric.

    Args:
        time (datetime): Input event origin time.
        lat (float): Input event latitude.
        lon (float): Input event longitude.
        twindow (float): Time search window in seconds.
        radius (float): Search distance window in km.
    Returns:
        DataFrame: pandas DataFrame containing columns:
         - id ComCat Event ID
         - time Authoritative event time
         - latitude Authoritative event latitude
         - longitude Authoritative event longitude
         - magnitude Authoritative event magnitude
         - distance(km) Distance from input event in km
         - timedelta(sec) Time difference from input event in seconds
         - azimuth(deg) Azimuth from input event to event in this row.
         - normalized_time_dist_vector Result of:
             sqrt((dd/radius)^2 + (dt/window)^2),
           where dd is distance, and dt is time delta.
    """
    start_time = time - timedelta(seconds=twindow)
    end_time = time + timedelta(seconds=twindow)
    events = search(starttime=start_time,
                    endtime=end_time,
                    latitude=lat,
                    longitude=lon,
                    maxradiuskm=radius)

    if not len(events):
        return None

    df = get_summary_data_frame(events)

    # drop the pager alert level and location strings,
    # as they aren't really needed in this context
    df = df.drop(labels=['alert', 'location'], axis='columns')

    df['distance(km)'] = 0
    df['timedelta(sec)'] = 0
    df['azimuth(deg)'] = 0
    df['normalized_time_dist_vector'] = 0
    for idx, row in df.iterrows():
        distance, az, azb = gps2dist_azimuth(
            lat, lon, row['latitude'], row['longitude'])
        distance_km = distance / 1000
        row_time = row['time'].to_pydatetime()
        dtime = row_time - time
        dt = np.abs(dtime.days * 86400 + dtime.seconds)
        df.loc[idx, 'distance(km)'] = distance_km
        df.loc[idx, 'timedelta(sec)'] = dt
        df.loc[idx, 'azimuth(deg)'] = az
        dt_norm = dt / twindow
        dd_norm = distance_km / radius
        norm_vec = np.sqrt(dt_norm**2 + dd_norm**2)
        df.loc[idx, 'normalized_time_dist_vector'] = norm_vec

    # reorder the columns so that url is at the end
    cols = ['id', 'time', 'latitude', 'longitude', 'depth', 'magnitude',
            'distance(km)', 'timedelta(sec)', 'azimuth(deg)',
            'normalized_time_dist_vector', 'url']
    df = df[cols]
    df = df.sort_values('normalized_time_dist_vector', axis='index')
    return df
