# stdlib imports
import logging
import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlparse

import dateutil
import numpy as np
import pandas as pd
import requests

# third party imports
from obspy.core.event import read_events

# local imports
from libcomcat.exceptions import (
    ArgumentConflictError,
    ConnectionError,
    ContentNotFoundError,
    ProductNotFoundError,
    UndefinedVersionError,
)
from libcomcat.utils import HEADERS, TIMEOUT

# constants
# the detail event URL template
URL_TEMPLATE = (
    "https://earthquake.usgs.gov/earthquakes/feed" "/v1.0/detail/[EVENTID].geojson"
)
# the search template for a detail event that may
# include one or both of includesuperseded/includedeleted.
SEARCH_DETAIL_TEMPLATE = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson&eventid=%s&"
    "includesuperseded=%s&includedeleted=%s"
)
SCENARIO_SEARCH_DETAIL_TEMPLATE = (
    "https://earthquake.usgs.gov/fdsnws/scenario/1/query"
    "?format=geojson&eventid=%s&"
    "includesuperseded=%s&includedeleted=%s"
)
WAITSECS = 3


def _get_moment_tensor_info(tensor, get_angles=False, get_moment_supplement=False):
    """Internal - gather up tensor components and focal mechanism angles.

    Args:
        tensor:
        get_angles(bool):
        get_moment_supplement(bool):
    """
    msource = tensor["eventsource"]
    if tensor.hasProperty("derived-magnitude-type"):
        msource += "_" + tensor["derived-magnitude-type"]
    elif tensor.hasProperty("beachball-type"):
        btype = tensor["beachball-type"]
        if btype.find("/") > -1:
            btype = btype.split("/")[-1]
        msource += "_" + btype

    edict = OrderedDict()
    edict["%s_mrr" % msource] = float(tensor["tensor-mrr"])
    edict["%s_mtt" % msource] = float(tensor["tensor-mtt"])
    edict["%s_mpp" % msource] = float(tensor["tensor-mpp"])
    edict["%s_mrt" % msource] = float(tensor["tensor-mrt"])
    edict["%s_mrp" % msource] = float(tensor["tensor-mrp"])
    edict["%s_mtp" % msource] = float(tensor["tensor-mtp"])
    if get_angles and tensor.hasProperty("nodal-plane-1-strike"):
        edict["%s_np1_strike" % msource] = float(tensor["nodal-plane-1-strike"])
        edict["%s_np1_dip" % msource] = float(tensor["nodal-plane-1-dip"])
        if tensor.hasProperty("nodal-plane-1-rake"):
            edict["%s_np1_rake" % msource] = float(tensor["nodal-plane-1-rake"])
        else:
            edict["%s_np1_rake" % msource] = float(tensor["nodal-plane-1-slip"])
        edict["%s_np2_strike" % msource] = float(tensor["nodal-plane-2-strike"])
        edict["%s_np2_dip" % msource] = float(tensor["nodal-plane-2-dip"])
        if tensor.hasProperty("nodal-plane-2-rake"):
            edict["%s_np2_rake" % msource] = float(tensor["nodal-plane-2-rake"])
        else:
            edict["%s_np2_rake" % msource] = float(tensor["nodal-plane-2-slip"])

    if get_moment_supplement:
        if tensor.hasProperty("derived-latitude"):
            edict["%s_derived_latitude" % msource] = float(tensor["derived-latitude"])
            edict["%s_derived_longitude" % msource] = float(tensor["derived-longitude"])
            edict["%s_derived_depth" % msource] = float(tensor["derived-depth"])
        if tensor.hasProperty("percent-double-couple"):
            edict["%s_percent_double_couple" % msource] = float(
                tensor["percent-double-couple"]
            )
        if tensor.hasProperty("sourcetime-duration"):
            edict["%s_sourcetime_duration" % msource] = float(
                tensor["sourcetime-duration"]
            )

    return edict


def _get_focal_mechanism_info(focal):
    """Internal - gather up focal mechanism angles.

    Args:
        focal():
    """
    msource = focal["eventsource"]
    eventid = msource + focal["eventsourcecode"]
    edict = OrderedDict()
    try:
        edict["%s_np1_strike" % msource] = float(focal["nodal-plane-1-strike"])
    except Exception:
        logging.warning("No focal angles for %s in detailed geojson.\n" % eventid)
        return edict
    edict["%s_np1_dip" % msource] = float(focal["nodal-plane-1-dip"])
    if focal.hasProperty("nodal-plane-1-rake"):
        edict["%s_np1_rake" % msource] = float(focal["nodal-plane-1-rake"])
    else:
        edict["%s_np1_rake" % msource] = float(focal["nodal-plane-1-slip"])
    edict["%s_np2_strike" % msource] = float(focal["nodal-plane-2-strike"])
    edict["%s_np2_dip" % msource] = float(focal["nodal-plane-2-dip"])
    if focal.hasProperty("nodal-plane-2-rake"):
        edict["%s_np2_rake" % msource] = float(focal["nodal-plane-2-rake"])
    else:
        edict["%s_np2_rake" % msource] = float(focal["nodal-plane-2-slip"])
    return edict


class SummaryEvent(object):
    """Wrapper around summary feature as returned by ComCat GeoJSON search results."""

    def __init__(self, feature):
        """Instantiate a SummaryEvent object with a feature.

        See summary documentation here:

        https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php

        Args:
            feature (dict): GeoJSON feature as described at above URL.
        """
        self._jdict = feature.copy()

    @property
    def location(self):
        """Earthquake location string.

        Returns:
            str: Earthquake location.
        """
        return self._jdict["properties"]["place"]

    @property
    def url(self):
        """ComCat URL.

        Returns:
            str: ComCat URL
        """
        return self._jdict["properties"]["url"]

    @property
    def latitude(self):
        """Authoritative origin latitude.

        Returns:
            float: Authoritative origin latitude.
        """
        return self._jdict["geometry"]["coordinates"][1]

    @property
    def longitude(self):
        """Authoritative origin longitude.

        Returns:
            float: Authoritative origin longitude.
        """
        return self._jdict["geometry"]["coordinates"][0]

    @property
    def depth(self):
        """Authoritative origin depth.

        Returns:
            float: Authoritative origin depth.
        """
        depth = self._jdict["geometry"]["coordinates"][2]
        if depth is None:
            depth = np.nan
        return depth

    @property
    def id(self):
        """Authoritative origin ID.

        Returns:
            str: Authoritative origin ID.
        """
        return self._jdict["id"]

    @property
    def time(self):
        """Authoritative origin time.

        Returns:
            dt (datetime): Authoritative origin time.
        """
        time_in_msec = self._jdict["properties"]["time"]
        time_in_sec = time_in_msec // 1000
        msec = time_in_msec - (time_in_sec * 1000)
        # utcfromtimestamp() raises an exception
        # on Windows when input seconds are negative (prior to 1970)
        # what follows is a workaround
        dtime = datetime(1970, 1, 1) + timedelta(seconds=time_in_sec)
        dt = timedelta(milliseconds=msec)
        dtime = dtime + dt
        return dtime

    @property
    def magnitude(self):
        """Authoritative origin magnitude.

        Returns:
            float: Authoritative origin magnitude.
        """
        magvalue = self._jdict["properties"]["mag"]
        if magvalue is None:
            magvalue = np.nan
        return magvalue

    @property
    def alert(self):
        """PAGER summary alert level (or '' if not present).

        Returns:
            str: PAGER alert level ('green', 'yellow', 'orange', 'red').
        """
        return self._jdict["properties"]["alert"]

    def __repr__(self):
        tpl = (
            self.id,
            str(self.time),
            self.latitude,
            self.longitude,
            self.depth,
            self.magnitude,
        )
        return "%s %s (%.3f,%.3f) %.1f km M%.1f" % tpl

    @property
    def properties(self):
        """List of summary event properties.

        Returns:
            list: List of summary event properties (retrievable
                  from object with [] operator).
        """
        return list(self._jdict["properties"].keys())

    def hasProduct(self, product):
        """Test to see whether a given product exists for this event.

        Args:
            product (str): Product to search for.
        Returns:
            bool: Indicates whether that product exists or not.
        """
        if product not in self._jdict["properties"]["types"].split(",")[1:]:
            return False
        return True

    def hasProperty(self, key):
        """Test to see if property is present in list of properties.

        Args:
            key (str): Property to search for.
        Returns:
          bool: Indicates whether that key exists or not.
        """
        if key not in self._jdict["properties"]:
            return False
        return True

    def __getitem__(self, key):
        """Extract SummaryEvent property using the [] operator.

        Args:
            key (str): Property to extract.
        Returns:
            str: Desired property.
        """
        if key not in self._jdict["properties"]:
            raise AttributeError("No property %s found for event %s." % (key, self.id))
        return self._jdict["properties"][key]

    def getDetailURL(self):
        """Instantiate a DetailEvent object from the URL found in the summary.

        Returns:
            str: URL for detailed version of event.
        """
        durl = self._jdict["properties"]["detail"]
        return durl

    def getDetailEvent(
        self, includedeleted=False, includesuperseded=False, scenario=False
    ):
        """Instantiate a DetailEvent object from the URL found in the summary.

        Args:
            includedeleted (bool): Boolean indicating wheather to return
                versions of products that have
                been deleted. Cannot be used with
                includesuperseded.
            includesuperseded (bool):
                Boolean indicating wheather to return versions of products
                that have been replaced by newer versions.
                Cannot be used with includedeleted.
            scenario (bool): Indicates that the event ID in question is a scenario.
        Returns:
            DetailEvent: Detailed version of SummaryEvent.
        """
        if includesuperseded and includedeleted:
            msg = "includedeleted and includesuperseded " "cannot be used together."
            raise ArgumentConflictError(msg)
        if not includedeleted and not includesuperseded:
            durl = self._jdict["properties"]["detail"]
            return DetailEvent(durl)
        else:
            true_false = {True: "true", False: "false"}
            deleted = true_false[includedeleted]
            superseded = true_false[includesuperseded]
            if scenario:
                url = SCENARIO_SEARCH_DETAIL_TEMPLATE % (self.id, superseded, deleted)
            else:
                url = SEARCH_DETAIL_TEMPLATE % (self.id, superseded, deleted)
            return DetailEvent(url)

    def toDict(self):
        """Render the SummaryEvent origin information as an OrderedDict().

        Returns:
            dict: Containing fields:
               - id (string) Authoritative ComCat event ID.
               - time (datetime) Authoritative event origin time.
               - latitude (float) Authoritative event latitude.
               - longitude (float) Authoritative event longitude.
               - depth (float) Authoritative event depth.
               - magnitude (float) Authoritative event magnitude.
        """
        edict = OrderedDict()
        edict["id"] = self.id
        edict["time"] = self.time
        edict["location"] = self.location
        edict["latitude"] = self.latitude
        edict["longitude"] = self.longitude
        edict["depth"] = self.depth
        edict["magnitude"] = self.magnitude
        edict["alert"] = self.alert
        edict["url"] = self.url
        edict["eventtype"] = self._jdict["properties"]["type"]
        edict["significance"] = self["sig"]
        return edict


class DetailEvent(object):
    """Wrapper around detailed event as returned by ComCat GeoJSON search results."""

    def __init__(self, url):
        """Instantiate a DetailEvent object with a url pointing to detailed GeoJSON.

        See detailed documentation here:

        https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson_detail.php

        Args:
            url (str): String indicating a URL pointing to a detailed GeoJSON
                       event.
        """
        try:
            response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            self._jdict = response.json()
            self._actual_url = url
        except requests.exceptions.ReadTimeout:
            try:
                response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
                self._jdict = response.json()
                self._actual_url = url
            except Exception as msg:
                fmt = "Could not connect to ComCat server - %s."
                raise ConnectionError(fmt % url).with_traceback(msg.__traceback__)

    def __repr__(self):
        tpl = (
            self.id,
            str(self.time),
            self.latitude,
            self.longitude,
            self.depth,
            self.magnitude,
        )
        return "%s %s (%.3f,%.3f) %.1f km M%.1f" % tpl

    @property
    def location(self):
        """Earthquake location string.

        Returns:
            str: Earthquake location.
        """
        return self._jdict["properties"]["place"]

    @property
    def url(self):
        """ComCat URL.

        Returns:
            str: Earthquake URL.
        """
        return self._jdict["properties"]["url"]

    @property
    def detail_url(self):
        """ComCat Detailed URL (with JSON).

        Returns:
            str: Earthquake Detailed URL with JSON.
        """
        return self._actual_url

    @property
    def latitude(self):
        """Authoritative origin latitude.

        Returns:
            float: Authoritative origin latitude.
        """
        return self._jdict["geometry"]["coordinates"][1]

    @property
    def longitude(self):
        """Authoritative origin longitude.

        Returns:
            float: Authoritative origin longitude.
        """
        return self._jdict["geometry"]["coordinates"][0]

    @property
    def depth(self):
        """Authoritative origin depth."""
        depth = self._jdict["geometry"]["coordinates"][2]
        if depth is None:
            depth = np.nan

        return depth

    @property
    def id(self):
        """Authoritative origin ID.

        Returns:
            str: Authoritative origin ID.
        """
        return self._jdict["id"]

    @property
    def time(self):
        """Authoritative origin time.

        Returns:
            datetime: Authoritative origin time.
        """
        time_in_msec = self._jdict["properties"]["time"]
        time_in_sec = time_in_msec // 1000
        msec = time_in_msec - (time_in_sec * 1000)
        dtime = datetime(1970, 1, 1) + timedelta(seconds=time_in_sec)
        dt = timedelta(milliseconds=msec)
        dtime = dtime + dt
        return dtime

    @property
    def magnitude(self):
        """Authoritative origin magnitude.

        Returns:
            float: Authoritative origin magnitude.
        """
        return self._jdict["properties"]["mag"]

    @property
    def alert(self):
        """PAGER summary alert, or None if not present.

        Returns:
            str: PAGER summary alert, one of ('green','yellow','orange','red')
        """
        if self.hasProperty("alert"):
            return self["alert"]
        else:
            return None

    @property
    def properties(self):
        """List of detail event properties.

        Returns:
            list: List of summary event properties (retrievable from object
                  with [] operator).
        """
        return list(self._jdict["properties"].keys())

    @property
    def products(self):
        """List of detail event properties.

        Returns:
            list: List of detail event products (retrievable from object with
                getProducts() method).
        """
        return list(self._jdict["properties"]["products"].keys())

    def hasProduct(self, product):
        """Return a boolean indicating whether given product can be extracted
        from DetailEvent.

        Args:
            product (str): Product to search for.
        Returns:
            bool: Indicates whether that product exists or not.
        """
        if product in self._jdict["properties"]["products"]:
            return True
        return False

    def hasProperty(self, key):
        """Test to see whether a property with a given key is present property list.

        Args:
            key (str): Property to search for.
        Returns:
            bool: Indicates whether that key exists or not.
        """
        c1 = "properties" not in self._jdict
        c2 = key not in self._jdict["properties"]
        if c1 or c2:
            return False
        return True

    def __getitem__(self, key):
        """Extract DetailEvent property using the [] operator.

        Args:
            key (str): Property to extract.
        Returns:
            str: Desired property.
        """
        if key not in self._jdict["properties"]:
            raise AttributeError("No property %s found for event %s." % (key, self.id))
        return self._jdict["properties"][key]

    def toDict(
        self,
        catalog=None,
        get_all_magnitudes=False,
        get_tensors="preferred",
        get_moment_supplement=False,
        get_focals="preferred",
    ):
        """Return origin, focal mechanism, and tensor information for a DetailEvent.

        Args:
            catalog (str): Retrieve the primary event information (time,lat,
                lon...) from the catalog given. If no source for this
                information exists, an AttributeError will be raised.
            get_all_magnitudes (bool): Indicates whether all known magnitudes
                for this event should be returned. NOTE: The ComCat phase-data
                product's QuakeML file will be downloaded and parsed, which
                takes extra time.
            get_tensors (str): Option of 'none', 'preferred', or 'all'.
            get_moment_supplement (bool): Boolean indicating whether derived
            origin and double-couple/source time information should be
            extracted (when available.)
            get_focals (str): String option of 'none', 'preferred', or 'all'.
        Returns:
            edict: OrderedDict with the same fields as returned by
                SummaryEvent.toDict(), *preferred* moment tensor and focal
                mechanism data.  If all magnitudes are requested, then
                those will be returned as well. Generally speaking, the
                number and name of the fields will vary by what data is
                available.
        """
        edict = OrderedDict()

        if catalog is None:
            edict["id"] = self.id
            edict["time"] = self.time
            edict["location"] = self.location
            edict["latitude"] = self.latitude
            edict["longitude"] = self.longitude
            edict["depth"] = self.depth
            edict["magnitude"] = self.magnitude
            edict["magtype"] = self._jdict["properties"]["magType"]
            edict["url"] = self.url
            edict["eventtype"] = self._jdict["properties"]["type"]
            edict["alert"] = self.alert
            edict["significance"] = self["sig"]
        else:
            try:
                phase_sources = []
                origin_sources = []
                if self.hasProduct("phase-data"):
                    phase_sources = [
                        p.source for p in self.getProducts("phase-data", source="all")
                    ]
                if self.hasProduct("origin"):
                    origin_sources = [
                        o.source for o in self.getProducts("origin", source="all")
                    ]
                if catalog in phase_sources:
                    phasedata = self.getProducts("phase-data", source=catalog)[0]
                elif catalog in origin_sources:
                    phasedata = self.getProducts("origin", source=catalog)[0]
                else:
                    msg = (
                        "DetailEvent %s has no phase-data or origin "
                        "products for source %s"
                    )
                    raise ProductNotFoundError(msg % (self.id, catalog))
                edict["id"] = phasedata["eventsource"] + phasedata["eventsourcecode"]
                edict["time"] = dateutil.parser.parse(phasedata["eventtime"])
                edict["location"] = self.location
                edict["latitude"] = float(phasedata["latitude"])
                edict["longitude"] = float(phasedata["longitude"])
                edict["depth"] = float(phasedata["depth"])
                edict["magnitude"] = float(phasedata["magnitude"])
                edict["magtype"] = phasedata["magnitude-type"]
                edict["alert"] = self.alert
            except AttributeError as ae:
                raise ae

        if get_tensors == "all":
            if self.hasProduct("moment-tensor"):
                tensors = self.getProducts("moment-tensor", source="all", version="all")
                for tensor in tensors:
                    supp = get_moment_supplement
                    tdict = _get_moment_tensor_info(
                        tensor, get_angles=True, get_moment_supplement=supp
                    )
                    edict.update(tdict)

        if get_tensors == "preferred":
            if self.hasProduct("moment-tensor"):
                tensor = self.getProducts("moment-tensor")[0]
                supp = get_moment_supplement
                tdict = _get_moment_tensor_info(
                    tensor, get_angles=True, get_moment_supplement=supp
                )
                edict.update(tdict)

        if get_focals == "all":
            if self.hasProduct("focal-mechanism"):
                focals = self.getProducts(
                    "focal-mechanism", source="all", version="all"
                )
                for focal in focals:
                    edict.update(_get_focal_mechanism_info(focal))

        if get_focals == "preferred":
            if self.hasProduct("focal-mechanism"):
                focal = self.getProducts("focal-mechanism")[0]
                edict.update(_get_focal_mechanism_info(focal))

        if get_all_magnitudes:
            phases = []
            if self.hasProduct("phase-data"):
                phase_products = self.getProducts("phase-data", source="all")
                phases += phase_products
            if self.hasProduct("origin"):
                origin_products = self.getProducts("origin", source="all")
                phases += origin_products
            imag = 0
            unique_magnitudes = []
            for phase_data in phases:
                # we don't want duplicates of phase data information
                # from us origin product
                # this prevents us from getting non-authoritative mags
                # from preferred source. Commenting out.
                # ######################################
                # if product == 'origin' and phase_data.source == 'us':
                #     continue
                # ######################################
                phase_url = phase_data.getContentURL("quakeml.xml")
                try:
                    catalog = read_events(phase_url, format="QUAKEML")
                except Exception as e:
                    catalog = read_events(phase_url, format="QUAKEML")
                    fmt = "Could not parse quakeml file from %s. " "Error: %s"
                    tpl = (phase_url, str(e))
                    logging.warning(fmt % tpl)
                    continue
                event = catalog.events[0]
                for magnitude in event.magnitudes:
                    # since resource IDs for magnitudes are unique, we can use this
                    # to track whether we're getting duplicate magnitudes
                    # from phase-data and origin products.
                    magid = magnitude.resource_id.id
                    if magid in unique_magnitudes:
                        continue
                    unique_magnitudes.append(magid)
                    edict["magnitude%i" % imag] = magnitude.mag
                    edict["magtype%i" % imag] = magnitude.magnitude_type
                    cname = "magsource%i" % imag
                    if magnitude.creation_info is not None:
                        edict[cname] = magnitude.creation_info.agency_id
                    else:
                        if event.creation_info is not None:
                            edict[cname] = event.creation_info.agency_id
                        else:
                            edict[cname] = ""
                    imag += 1

        return edict

    def getNumVersions(self, product_name):
        """Count versions of a product (origin, shakemap, etc.) available.

        Args:
            product_name (str): Name of product to query.
        Returns:
            int: Number of versions of a given product.
        """
        if not self.hasProduct(product_name):
            raise ProductNotFoundError(
                "Event %s has no product of type %s" % (self.id, product_name)
            )
        return len(self._jdict["properties"]["products"][product_name])

    def getProducts(self, product_name, source="preferred", version="preferred"):
        """Retrieve a Product object from this DetailEvent.

        Args:
            product_name (str): Name of product (origin, shakemap, etc.) to
                                retrieve.
            version (enum): Any one of:
                - 'preferred' Get the preferred version.
                - 'first' Get the first version.
                - 'last' Get the last version.
                - 'all' Get all versions.
            source (str): Any one of:
                - 'preferred' Get version(s) of products from preferred source.
                - 'all' Get version(s) of products from all sources.
                - Any valid source network for this type of product
                  ('us','ak',etc.)
        Returns:
          list: List of Product objects.
        """
        if version not in ["preferred", "first", "last", "all"]:
            msg = "No version defined for %s" % version
            raise (UndefinedVersionError(msg))
        if not self.hasProduct(product_name):
            raise ProductNotFoundError(
                "Event %s has no product of type %s" % (self.id, product_name)
            )

        products = self._jdict["properties"]["products"][product_name]
        weights = [product["preferredWeight"] for product in products]
        sources = [product["source"] for product in products]
        times = [product["updateTime"] for product in products]
        indices = list(range(0, len(times)))
        df = pd.DataFrame(
            {"weight": weights, "source": sources, "time": times, "index": indices}
        )

        # add a datetime column for debugging
        df["datetime"] = (df["time"] / 1000).apply(datetime.utcfromtimestamp)

        # we need to add a version number column here, ordinal
        # sorted by update time, starting at 1
        # for each unique source.
        # first sort the dataframe by source and then time
        psources = df["source"].unique()
        newframe = pd.DataFrame(columns=df.columns.to_list() + ["version"])
        for psource in psources:
            dft = df[df["source"] == psource]
            dft = dft.sort_values("time")
            dft["version"] = np.arange(1, len(dft) + 1)
            newframe = pd.concat([newframe, dft])
        df = newframe

        if source == "preferred":
            idx = weights.index(max(weights))
            tproduct = self._jdict["properties"]["products"][product_name][idx]
            prefsource = tproduct["source"]
            df = df[df["source"] == prefsource]
            df = df.sort_values("time")
        elif source == "all":
            df = df.sort_values(["source", "time"])
        else:
            df = df[df["source"] == source]
            df = df.sort_values("time")

        # if we don't have any versions of products, raise an exception
        if not len(df):
            raise ProductNotFoundError('No products found for source "%s".' % source)

        products = []
        usources = set(sources)
        tproducts = self._jdict["properties"]["products"][product_name]
        if source == "all":  # dataframe includes all sources
            for usource in usources:
                df_source = df[df["source"] == usource]
                df_source = df_source.sort_values("time")
                if version == "preferred":
                    df_source = df_source.sort_values(["weight", "time"])
                    idx = df_source.iloc[-1]["index"]
                    pversion = df_source.iloc[-1]["version"]
                    product = Product(product_name, pversion, tproducts[idx])
                    products.append(product)
                elif version == "last":
                    idx = df_source.iloc[-1]["index"]
                    pversion = df_source.iloc[-1]["version"]
                    product = Product(product_name, pversion, tproducts[idx])
                    products.append(product)
                elif version == "first":
                    idx = df_source.iloc[0]["index"]
                    pversion = df_source.iloc[0]["version"]
                    product = Product(product_name, pversion, tproducts[idx])
                    products.append(product)
                elif version == "all":
                    for idx, row in df_source.iterrows():
                        idx = row["index"]
                        pversion = row["version"]
                        product = Product(product_name, pversion, tproducts[idx])
                        products.append(product)
        else:  # dataframe only includes one source
            if version == "preferred":
                df = df.sort_values(["weight", "time"])
                idx = df.iloc[-1]["index"]
                pversion = df.iloc[-1]["version"]
                product = Product(product_name, pversion, tproducts[idx])
                products.append(product)
            elif version == "last":
                idx = df.iloc[-1]["index"]
                pversion = df.iloc[-1]["version"]
                product = Product(product_name, pversion, tproducts[idx])
                products.append(product)
            elif version == "first":
                idx = df.iloc[0]["index"]
                pversion = df.iloc[0]["version"]
                product = Product(product_name, pversion, tproducts[idx])
                products.append(product)
            elif version == "all":
                for idx, row in df.iterrows():
                    idx = row["index"]
                    pversion = row["version"]
                    product = Product(product_name, pversion, tproducts[idx])
                    products.append(product)

        return products


class Product(object):
    """Class describing a Product from detailed GeoJSON feed."""

    def __init__(self, product_name, version, product):
        """Create a product class from product in detailed GeoJSON.

        Args:
            product_name (str): Name of Product (origin, shakemap, etc.)
            version (int): Best guess as to ordinal version of the product.
            product (dict): Product data to be copied from DetailEvent.
        """
        self._product_name = product_name
        self._version = version
        self._product = product.copy()

    def getContentsMatching(self, regexp):
        """Find all contents that match the input regex, shortest to longest.

        Args:
            regexp (str): Regular expression which should match one of the
                          content files in the Product.
        Returns:
            list: List of contents matching input regex.
        """
        contents = []
        if not len(self._product["contents"]):
            return contents

        for contentkey in self._product["contents"].keys():
            if "url" not in self._product["contents"][contentkey]:
                continue
            url = self._product["contents"][contentkey]["url"]
            parts = urlparse(url)
            fname = parts.path.split("/")[-1]
            if re.search(regexp + "$", fname):
                contents.append(fname)
        return contents

    def __repr__(self):
        ncontents = len(self._product["contents"])
        tpl = (self._product_name, self.source, self.update_time, ncontents)
        return "Product %s from %s updated %s " "containing %i content files." % tpl

    def getContentName(self, regexp):
        """Get the shortest filename matching input regular expression.

        For example, if the shakemap product has contents called
        grid.xml and grid.xml.zip, and the input regexp is grid.xml,
        then grid.xml will be matched.

        Args:
            regexp (str): Regular expression to use to search for
                          matching contents.
        Returns:
            str: Shortest file name to match input regexp, or None if
                 no matches found.
        """
        content_name = "a" * 1000
        found = False
        contents = self._product["contents"]
        if not len(contents):
            return None
        for contentkey, content in self._product["contents"].items():
            if re.search(regexp + "$", contentkey) is None:
                continue
            url = content["url"]
            parts = urlparse(url)
            fname = parts.path.split("/")[-1]
            if len(fname) < len(content_name):
                content_name = fname
                found = True
        if found:
            return content_name
        else:
            return None

    def getContentURL(self, regexp):
        """Get the URL for the shortest filename matching input regular expression.

        For example, if the shakemap product has contents called grid.xml and
        grid.xml.zip, and the input regexp is grid.xml, then grid.xml will be
        matched.

        Args:
            regexp (str): Regular expression to use to search for matching
                          contents.
        Returns:
            str: URL for shortest file name to match input regexp, or
                 None if no matches found.
        """
        content_name = "a" * 1000
        found = False
        content_url = ""
        if "contents" not in self._product:
            return None
        if not len(self._product["contents"]):
            return None
        for contentkey, content in self._product["contents"].items():
            if re.search(regexp + "$", contentkey) is None:
                continue
            url = content["url"]
            parts = urlparse(url)
            fname = parts.path.split("/")[-1]
            if len(fname) < len(content_name):
                content_name = fname
                content_url = url
                found = True
        if found:
            return content_url
        else:
            return None

    def getContent(self, regexp, filename):
        """Download the shortest file name matching the input regular expression.

        Args:
            regexp (str): Regular expression which should match one of the
                content files
                in the Product.
            filename (str): Filename to which content should be downloaded.
        Returns:
            str: The URL from which the content was downloaded.
        Raises:
          Exception: If content could not be downloaded from ComCat
              after two tries.
        """
        data, url = self.getContentBytes(regexp)

        f = open(filename, "wb")
        f.write(data)
        f.close()

        return url

    def getContentBytes(self, regexp):
        """Return bytes of shortest file name matching input regular expression.


        Args:
            regexp (str): Regular expression which should match one of the
                content files in
                the Product.
        Returns:
            tuple: (array of bytes containing file contents, source url)
                Bytes can be decoded to UTF-8 by the user if file contents
                are known to be ASCII.  i.e.,
                product.getContentBytes('info.json').decode('utf-8')
        Raises:
            Exception: If content could not be downloaded from ComCat
                after two tries.
        """
        content_name = "a" * 1000
        content_url = None
        for contentkey, content in self._product["contents"].items():
            if re.search(regexp + "$", contentkey) is None:
                continue
            url = content["url"]
            parts = urlparse(url)
            fname = parts.path.split("/")[-1]
            if len(fname) < len(content_name):
                content_name = fname
                content_url = url
        if content_url is None:
            # TODO make better exception
            raise ContentNotFoundError(
                "Could not find any content matching input %s" % regexp
            )

        try:
            response = requests.get(url, timeout=TIMEOUT, stream=True, headers=HEADERS)
            data = response.content

        except HTTPError:
            time.sleep(WAITSECS)
            try:
                response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
                data = response.content
            except Exception:
                raise ConnectionError(
                    "Could not download %s from %s." % (content_name, url)
                )

        return (data, url)

    def hasProperty(self, key):
        """Determine if this Product contains a given property.

        Args:
            key (str): Property to search for.
        Returns:
            bool: Indicates whether that key exists or not.
        """
        c1 = "properties" not in self._product
        c2 = c1 or key not in self._product["properties"]
        if c2:
            return False
        return True

    @property
    def name(self):
        return self._product_name

    @property
    def preferred_weight(self):
        """The weight assigned to this product by ComCat.

        Returns:
            float: weight assigned to this product by ComCat.
        """
        return self._product["preferredWeight"]

    @property
    def source(self):
        """The contributing source for this product.

        Returns:
            str: contributing source for this product.
        """
        return self._product["source"]

    @property
    def product_timestamp(self):
        """The timestamp for this product.

        Returns:
            int: The timestamp for this product (effectively used as
                version number by ComCat).
        """
        time_in_msec = self._product["updateTime"]
        return time_in_msec

    @property
    def update_time(self):
        """The datetime for when this product was updated.

        Returns:
            datetime: datetime for when this product was updated.
        """
        time_in_msec = self._product["updateTime"]
        time_in_sec = time_in_msec // 1000
        msec = time_in_msec - (time_in_sec * 1000)
        dtime = datetime.utcfromtimestamp(time_in_sec)
        dt = timedelta(milliseconds=msec)
        dtime = dtime + dt
        return dtime

    @property
    def version(self):
        """The best guess for the ordinal version number of this product.

        Returns:
            int: best guess for the ordinal version number of this product.
        """
        return self._version

    @property
    def properties(self):
        """List of product properties.

        Returns:
            list: List of product properties (retrievable from object
                  with [] operator).
        """
        return list(self._product["properties"].keys())

    @property
    def contents(self):
        """List of product properties.

        Returns:
            list: List of product properties (retrievable with
                  getContent() method).
        """
        if not len(self._product["contents"]):
            return []
        return list(self._product["contents"].keys())

    def __getitem__(self, key):
        """Extract Product property using the [] operator.

        Args:
            key (str): Property to extract.
        Returns:
            str: Desired property.
        """
        c1 = "properties" not in self._product
        c2 = c1 or key not in self._product["properties"]
        if c2:
            msg = "No property %s found in %s product." % (key, self._product_name)
            raise AttributeError(msg)
        return self._product["properties"][key]
