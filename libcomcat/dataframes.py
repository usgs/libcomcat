# stdlib imports
from collections import OrderedDict
from xml.dom import minidom
import sys
from urllib.request import urlopen
import warnings
import json
from io import StringIO
import re

# third party imports
import numpy as np
import pandas as pd
from obspy.io.quakeml.core import Unpickler
import requests
from scipy.special import erfcinv

# local imports
from libcomcat.classes import VersionOption


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
        fh = urlopen(quakeurl, timeout=TIMEOUT)
        data = fh.read()
        fh.close()
    except Exception:
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


def _get_phaserow(pick, catevent):
    """Return a dictionary containing Phase data matching that found on ComCat event page.
    Example: https://earthquake.usgs.gov/earthquakes/eventpage/us2000ahv0#origin
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
        fh = urlopen(quakeurl, timeout=TIMEOUT)
        data = fh.read()
        fh.close()
    except Exception:
        return None
    fmt = '%s.%s.%s.%s'
    unpickler = Unpickler()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        catalog = unpickler.loads(data)
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
        events (list): List of SummaryEvent objects as returned by search() function.
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
        get_all_versions (bool): Indicates whether to retrieve PAGER results for
            all versions.
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
            mmi10 - Estimated population exposed to shaking at MMI intensity 10.
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
    for pager in detail.getProducts('losspager', version=VersionOption.ALL):
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
    exposure_xml = pager.getContentBytes('pager.xml')[0].decode('utf-8')
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
        get_country_exposures (bool): Extract exposures for each affected country.
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
        tuple: (Dictionary of fatality G values, Dictionary of economic G values)

    """
    res = requests.get(FATALITY_URL)
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

    res = requests.get(ECONOMIC_URL)
    root = minidom.parseString(res.text)
    models = root.getElementsByTagName(
        'models')[0].getElementsByTagName('model')
    ecomodels = {}
    for model in models:
        ccode = model.getAttribute('ccode')
        if ccode in ccodes:
            ecomodels[ccode] = float(model.getAttribute('evalnormvalue'))
    root.unlink()

    return (fatmodels, ecomodels)


def get_impact_data_frame(detail, effect_types=None, loss_types=None,
                          loss_extents=None, all_sources=False, include_contributing=False,
                          source='preferred', version=VersionOption.PREFERRED):
    """Return a Pandas DataFrame consisting of impact data.

    Args:
        detail (DetailEvent): DetailEvent object.
        effect_types (list): List of requested effect types. Default is None.
        loss_types (list): List of requested loss types. Default is None.
        loss_extents (list): List of requested loss extents. Default is None.
        all_sources (bool): Include all sources including those that are
                not the most recent or authoritative. Default is False.
        include_contributing (bool): Include contributing features, not
                just the total summary. Default is False.
        source (str): Default is 'preferred'. Can be any one of:
                - 'preferred' Get version(s) of products from preferred source.
                - 'all' Get version(s) of products from all sources.
                - Any valid source network for this type of product ('us','ak',etc.)
        version (VersionOption): Product version. Default is VersionOption.PREFERRED.

    Returns:
        dataframe: Dataframe of the impact information.

    Raises:
        Exception: If the impact.json file cannot be read. Likely do to one
                not existing.
    """
    # Define spreadsheet columns and equivalent geojson keys
    columns = ['Source Network', 'ID', 'EventID', 'Time',
               'Magnitude', 'EffectType', 'LossType',
               'LossExtent', 'LossValue', 'LossMin',
               'LossMax', 'CollectionTime',
               'CollectionAuthor', 'CollectionSource',
               'Authoritative', 'Lat', 'Lon',
               'LossQuantifier', 'Comment']
    geojson_equivalent = {'EffectType': 'effect-type',
                          'LossType': 'loss-type',
                          'LossExtent': 'loss-extent',
                          'LossValue': 'loss-value',
                          'LossMin': 'loss-min',
                          'LossMax': 'loss-max',
                          'CollectionTime': 'collection-time',
                          'CollectionAuthor': 'collection-author',
                          'CollectionSource': 'collection-source',
                          'Authoritative': 'authoritative',
                          'LossQuantifier': 'loss-quantifier',
                          'Comment': 'comment'
                          }
    # Define valid parameters
    valid_effects = ['all', 'coal bump', 'dam failure', 'faulting', 'fire',
                     'geyser activity', 'ground cracking', 'landslide', 'lights', 'liquefaction',
                     'mine blast', 'mine collapse', 'odors', 'other', 'rockburst',
                     'sandblows', 'seiche', 'shaking', 'subsidence', 'tsunami',
                     'undifferentiated', 'uplift', 'volcanic activity']
    valid_loss_extents = ['damaged', 'damaged or destroyed', 'destroyed',
                          'displaced', 'injured', 'killed', 'missing']
    valid_loss_types = ['bridges', 'buildings', 'dollars', 'electricity',
                        'livestock', 'people', 'railroads', 'roads', 'telecommunications', 'water']

    # Convert arguments to lists
    if isinstance(effect_types, str):
        effect_types = [effect_types]
    if isinstance(loss_types, str):
        loss_types = [loss_types]
    if isinstance(loss_extents, str):
        loss_extents = [loss_extents]
    # Set defaults if no user input and validate options
    if effect_types is None:
        effect_types = valid_effects
    else:
        for effect in effect_types:
            if effect not in valid_effects:
                raise Exception('%r is not a valid effect type.' % effect)
    if loss_types is None:
        loss_types = valid_loss_types
        loss_types += ['']
    else:
        for loss in valid_loss_types:
            if loss not in valid_loss_types:
                raise Exception('%r is not a valid loss type.' % loss)
    if loss_extents is None:
        loss_extents = valid_loss_extents
        loss_extents += ['']
    else:
        for extent in loss_extents:
            if extent not in valid_loss_extents:
                raise Exception('%r is not a valid loss extent.' % extent)

    # Get the product(s)
    impacts = detail.getProducts('impact', source=source, version=version)
    table = OrderedDict()
    for col in columns:
        table[col] = []
    # Each product append to the OrderedDict
    for impact in impacts:
        # Attempt to read the json file
        impact_url = impact.getContentURL('impact.json')
        # Look for previous naming scheme
        if impact_url is None:
            impact_url = impact.getContentURL('.geojson')
        try:
            fh = urlopen(impact_url, timeout=TIMEOUT)
            file_text = fh.read().decode("utf-8")
            impact_data = json.loads(file_text)
            fh.close()
        except Exception as e:
            raise Exception('Unable to read impact.json for %s '
                            'which includes the file(s): %r' % (impact, impact.contents))
        features = impact_data['features']
        main_properties = {}
        # Get total feature lines
        for feature in features:
            # Impact-totals denotes the summary/total feature
            # This only considers summary/total features
            if 'impact-totals' in feature['properties']:
                main_properties['Time'] = feature['properties']['time']
                main_properties['ID'] = feature['properties']['id']
                main_properties['Source Network'] = feature['properties']['eventsource']
                main_properties['EventID'] = main_properties['Source Network'] + \
                    main_properties['ID']
                main_properties['Magnitude'] = feature['properties']['magnitude']
                for impact_total in feature['properties']['impact-totals']:
                        # Ensure that the "row" is valid
                    for column in columns:
                            # for totals the lat/lon fields are always empty
                        if column == 'Lat':
                            table['Lat'] += ['']
                        elif column == 'Lon':
                            table['Lon'] += ['']
                        elif column not in geojson_equivalent:
                            table[column] += [main_properties[column]]
                        else:
                            key = geojson_equivalent[column]
                            if key in impact_total:
                                table[column] += [impact_total[key]]
                            else:
                                table[column] += ['']
                break
        features.remove(feature)
        # Get contributing feature lines
        if include_contributing:
            for feature in features:
                # Ensure that the "row" is valid
                for column in columns:
                    if column == 'Lat':
                        lat = feature['geometry']['coordinates'][1]
                        table['Lat'] += [lat]
                    elif column == 'Lon':
                        lon = feature['geometry']['coordinates'][0]
                        table['Lon'] += [lon]
                    elif column not in geojson_equivalent:
                        table[column] += [main_properties[column]]
                    else:
                        key = geojson_equivalent[column]
                        if key in feature['properties']:
                            table[column] += [feature['properties'][key]]
                        else:
                            table[column] += ['']
    # Create the dataframe
    df = pd.DataFrame.from_dict(table)
    df = df[(df.LossExtent.isin(loss_extents))]
    df = df[(df.LossType.isin(loss_types))]
    df = df[(df.EffectType.isin(effect_types))]
    # Get most recent sources
    if not all_sources:
        df = df[(df.Authoritative == 1)]
    if not all_sources and len(df) > 1:
        df = _get_most_recent(df, effect_types, loss_extents, loss_types)
    return df


def _get_most_recent(df, effect_types, loss_extents, loss_types):
    """Get the most recent (most "trusted") source.

    Args:
        effect_types (list): List of requested effect types.
        loss_types (list): List of requested loss types.
        loss_extents (list): List of requested loss extents.
    Returns:
        dataframe: Dataframe without older sources.
    """
    drop_list = []
    for effect in effect_types:
        for loss in loss_types:
            for extent in loss_extents:
                boolean_df = df[(df.EffectType == effect) & (
                    df.LossType == loss) & (df.LossExtent == extent)]
                if len(boolean_df) > 0:
                    max_date = max(boolean_df['CollectionTime'])
                    idx = df.index[(df.EffectType == effect) & (df.LossType == loss) & (
                        df.LossExtent == extent) & (df.CollectionTime != max_date)].tolist()
                    drop_list += idx
    df = df.drop(set(drop_list))
    return df


def _validate_row(feature, feature_type, effect_types, loss_types, loss_extents,
                  all_sources, valid_effects, valid_loss_extents, valid_loss_types):
    """Validate that the row is valid based upon the requested parameters.

    Args:
        feature (dictionary): feature dictionary.
        feature_type (dictionary): Dictionary of the data row.
        effect_types (list): List of requested effect types. Default is None.
        loss_types (list): List of requested loss types. Default is None.
        loss_extents (list): List of requested loss extents. Default is None.
        all_sources (bool): Include all sources including those that are
                not the most recent or authoritative. Default is False.
        valid_effects (list): Valid effect types.
        valid_loss_types (list): Valid loss types.
        valid_loss_extents (list): Valid loss extents.

    Returns:
        bool: Whether or not the row is valid.
    """
    valid_row = True
    if feature_type == 'total':
        row = feature
    else:
        row = feature['properties']
    # Check source criteria
    if not all_sources and row['authoritative'] == 0:
        valid_row = False

    # Check loss_extent criteria
    if loss_extents != valid_loss_extents:
        if 'loss-extent' not in row:
            valid_row = False
        elif row['loss-extent'] not in loss_extents:
            valid_row = False

    # Check loss_type criteria
    if loss_types != valid_loss_types:
        if 'loss-type' not in row:
            valid_row = False
        elif row['loss-type'] not in loss_types:
            valid_row = False

    # Check loss_type criteria
    if effect_types != valid_effects:
        if 'effect-type' not in row:
            valid_row = False
        elif row['effect-type'] not in effect_types:
            valid_row = False
    return valid_row


def get_dyfi_data_frame(detail, dyfi_file=None, version=VersionOption.PREFERRED):
    """Retrieve a pandas DataFrame containing DYFI responses.

    Args:
        detail (DetailEvent): DetailEvent object.
        dyfi_file (str or None): If None, the file is chosen from the following list,
                                 in the order presented.
                                - utm_1km: UTM aggregated at 1km resolution.
                                - utm_10km: UTM aggregated at 10km resolution.
                                - utm_var: UTM aggregated "best" resolution for map.
                                - zip: ZIP/city aggregated.
        version (VersionOption): DYFI version. Default is VersionOption.PREFERRED.

    Returns:
        DataFrame or None: Pandas DataFrame containing columns:
            - station: Name of the location where aggregated responses are located.
            - lat: Latitude of responses.
            - lon: Longitude of responses.
            - distance: Distance from epicenter to location of aggregated responses.
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
