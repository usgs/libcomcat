

# Application Program Interface
----

The Application Program Interface (API), allows Python developers to query ComCat in ways that are not
supported by the Command Line Interface tools, and develop custom applications that use ComCat information
in unique ways.

## Contents
---
- [Searching](#Searching)
	- [Searching](#Searching)
		- [Time Parameters](#Time-Parameters)
		- [Location Parameters](#Location-Parameters)
		- [Preference Parameters](#Preference-Parameters)
		- [Other Parameters](#Other-Parameters)
	- [Count](#Count)
	- [Search by ID](#Search-by-ID)
- [Classes](#Classes)
	- [SummaryEvent](#SummaryEvent)
		- [Summary Properties](#Summary-Properties)
		- [Summary Class Methods](#Summary-Class-Methods)
	- [DetailEvent](#DetailEvent)
		- [Detail Properties](#Detail-Properties)
		- [Detail Class Methods](#Detail-Class-Methods)
	- [Product](#Product)
		- [Product Properties](#Product-Properties)
		- [Product Class Methods](#Product-Class-Methods)
- [Dataframes](#Dataframes)
	- [Summary Dataframe](#Summary-Dataframe)
	- [Detail Dataframe](#Detail-Dataframe)
	- [DYFI Dataframe](#DYFI-Dataframe)
	- [History Dataframe](#History-Dataframe)
	- [PAGER Dataframe](#PAGER-Dataframe)
	- [Magnitude Dataframe](#Magnitude-Dataframe)
	- [Phase Dataframe](#Phase-Dataframe)


---

## Searching
Searching for events in ComCat is the basis for all methods and classes in this library. All parameters for searching are based on the [ComCat API]([https://earthquake.usgs.gov/fdsnws/event/1/](https://earthquake.usgs.gov/fdsnws/event/1/).

See the [search Jupyter notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/Search.ipynb) for examples of these methods.

### Search
`from libcomcat.search import search`

The search method looks for events based upon ComCat's query parameters. The primary parameters define the time and location. The search method returns a [SummaryEvent Object](#SummaryEvent).


#### Time Parameters
API time inputs are datetime objects in UTC.

- Start Time: Events are limited to after the specified time. The default is 30 days before the time of search.
- End Time: Events are limited to on or before the time specified.  The default is the time of the search.
- Update Time: Events are limited to those that are updated after the specified time.

`time_events = search(starttime=datetime(1994, 1, 17, 12, 30), endtime=datetime(1994, 4, 18, 12, 35), updateafter=datetime(1994, 2, 18, 12, 35))`

#### Location Parameters
Latitude and longitude values should be in decimal degrees.

- Bounding Box: Limits events within minimum and maximum latitudes and longitudes. The minimum value must be smaller than the maximum value, but it can cross the dateline by using a minimum longitude less than -180 or a maximum longitude greater than 180. The default is the entire globe (minlatitude: -90, maxlatitude: 90, minlongitude: -180, maxlongitude: 180).
	- `box_events = search(starttime=datetime(1994, 1, 17, 12, 30), endtime=datetime(1994, 1, 18, 12, 35),minlatitude=34.1, maxlatitude=34.3, minlongitude=-118.742, maxlongitude=-118.364)`
- Radius search: If a target latitude and longitude is defined, a radius around it can be used to search for events. This can be done using a radius in kilometers or a radius in decimal degrees. The default is a 180 degree radius (defines the entire globe) and 20001.6 kilometer radius.
	- `deg_radius_events = search(starttime=datetime(1994, 1, 17, 12, 30), endtime=datetime(1994, 1, 18, 12, 35), maxradius=0.05, latitude=34.213, longitude=-118.537)`
	- `km_radius_events = search(starttime=datetime(1994, 1, 17, 12, 30), endtime=datetime(1994, 1, 18, 12, 35), maxradiuskm=2, latitude=34.213, longitude=-118.537)`
- Depth: Maximum and minimum depths in kilometers can limit events to a specific depth zone or threshold. The default minimum and maximum depths are -100 km and 1000 km respectively.
	- `depth_events = search(starttime=datetime(1994, 1, 17, 12, 30), endtime=datetime(1994, 1, 18, 12, 35), maxradiuskm=2, latitude=34.213, longitude=-118.537, maxdepth=15)`
- Azimuthal Gap: The azimuthal gap between adjacent stations can be defined by in degrees (between 0 and 180). Smaller azimuthal gaps can be used to calculated a more reliable horizontal position of earthquake. Larger azimuthal gaps (greater than 180) tend to result in larger location and depth uncertainty.
	- `az_events = search(starttime=datetime(1994, 1, 17, 12, 30), endtime=datetime(1994, 1, 18, 12, 35), mingap=0, maxgap=90)`


#### Preference Parameters
Preference parameters determine contributors, catalogs, and versions of parameters. Preferred catalogs, contributors, and versions are preferred products and are denoted by their [preferredWeight](https://earthquake.usgs.gov/data/comcat/data-productterms.php#product_preferredWeight).

- Catalog: Limits the events to those from an [available catalog](https://earthquake.usgs.gov/fdsnws/event/1/catalogs). (Link shows an XML document where the available catalogs are enclosed by <Catalog> tags.) The default is the 'preferred' catalog.
	- `us_events = search(catalog='us')`
- Contributor: Limits events by [available contributor](https://earthquake.usgs.gov/fdsnws/event/1/contributors).  (Link shows an XML document where the available catalogs are enclosed by <Contributor> tags.) The default is the 'preferred' contributor.
	- `ak_events = search(contributor='ak')`
- Host: By default the ComCat host is **earthquake.usgs.gov**, but this can be overriden using the host option.
	- `host_events = search(host='other_host')`
- Scenario: By default, libcomcat searches for real events. Use the --scenario option to search for scenario events.
- Products: If events with specific product(s) are desired, either the `producttype` or  `productcode` options can be used. The product type refers to the [product name](https://usgs.github.io/pdl/userguide/products/index.html). The product code is specific to the event and the product.
	- `product_type = search(producttype='shakemap')`
	- `product_code = search(productcode='nn00458749')`
- Event type: Events can be filtered by the type of event. For example, if only earthquake events are wanted, the event type should be set to earthquake. By default, the search is restricted to earthquakes.
	- `earthquake_events = search(eventtype='earthquake')`
- Review status: Review statuses are 'automatic' or 'reviewed'.
	- `reviewed_events = search(reviewstatus='reviewed')`

#### Magnitude and Intensity Parameters
Search results based upon descriptors for magnitude.

- Magnitude: A minimum and maximum magnitude can be defined to limit events. The default minimum and maximum magnitudes are 0 and 10 respectively.
	- `mag_events = search(minmagnitude=4, maxmagnitude=8)`
- Alert Level: If a PAGER alert level (green, yellow, orange, or red), the events with that alert level will be returned. **This is not a threshold, meaning that a search for orange events will return orange events, not orange and red**. If no PAGER product is available for the event, then the event will not be returned (even if significant losses may have occurred). This is will occur for small events and events that occurred before PAGER was available.
	- `alert_events = search(alertlevel="orange")`
- Maximum MMI: Thresholds events by the Maximum Modified Mercalli Intensity reported by Shakemap. This value can be 0-12. If no Shakemap product is available for the event, then it will not be returned.
	- `alert_events = search(maxmmi=5)`
- Significance: Events can be limited by the ComCat significance. A significance value is calculated for the magnitude (SM), for PAGER (SP), and for Did You Feel It (SD).


<img src="https://render.githubusercontent.com/render/math?math=SM=magnitude*100*\frac{magnitude}{6.5}">

<img src="https://render.githubusercontent.com/render/math?math=SP=\begin{bmatrix}red:2000\\orange:1000\\yellow:500\\green:0\end{bmatrix}">


<img src="https://render.githubusercontent.com/render/math?math=SD=min(N_{responses},1000)*\frac{CDI_{max}}{10}">

In the above equation CDImax is the maximum community determined intensity reported by Did You Feel It, and Nresponses is the number of responses. This is used to calculate the overall significance (S). If that value is greater than 600, it is considered a significant event and will appear on the [significant event list](https://earthquake.usgs.gov/earthquakes/browse/significant.php).

<img src="https://render.githubusercontent.com/render/math?math=S=max(SM,SP)"> + <img src="https://render.githubusercontent.com/render/math?math=SD">

- CDI: The community determined/decimal intensity (CDI) that is reported by Did You Feel It (DYFI) ranges between 0 and 12, similar to maximum MMI.
	- `cdi_events = search(mincdi=2, maxcdi=7)`
- Minimum Felt: DYFI also reports the number of responses. The number of people that felt and reported shaking can be used as a threshold.
	- `felt_events = search(minfelt=500)`

#### Other Parameters
Other parameters are related to the order and output of the search method.

- Limit: libcomcat works around the standard 20,000 event limit set up by ComCat, but if a limit is desired, it can be set. You can also enable the default 20,000 search limit using `enable_limit`.
	- `limit_events = search(limit=20)`
	- `limit_events = search(enable_limit=True)`
- Offset: The offset is defined by an integer between 1 and infinity. For the returned events, start at the event count denoted by the offset. By default there is no offest and the first event is shown (offset=1).
	- `second_event = search(offset=2)`
- Ordered Output: Events can be ordered by magnitude or time. `time` or `magnitude` will order events in descending order. To specify ascending order `-asc` must be added to the order parameter. The default is 'time-asc'.
	- `magnitude_events = search(orderby='magnitude')`
	- `magnitude_ascending_events = search(orderby='magnitude-asc')`
	- `time_events = search(orderby='time')`
	- `time_ascending_events = search(orderby='time-asc')`


### Count
`from libcomcat.search import count`

The count method returns the number of events that match a defined criteria. This is defined by the ComCat web API's count functionality. The input parameters for count are the same as those for the search method.

**NOTE:** The count method has not been shown to be any faster than the search method. If any data is needed, it would make more sense to search and then count the number of returned events rather than using `count` and `search` separately.


### Search by ID

`from libcomcat.search import get_event_by_id`

The get_event_by_id method assumes that the ComCat ID is already known. This method returns a [DetailEvent Object](#DetailEvent) which gives the user access to products and product contents.

####  Parameters
`get_event_by_id` has fewer parameters than the `search` and `count` methods.

- Event ID: The event id. This may be specific to the data center.
	- `ci3144585 = search(eventid='ci3144585')`
- Catalog: Limits the events to those from an [available catalog](https://earthquake.usgs.gov/fdsnws/event/1/catalogs). The default is the 'preferred' catalog.
	- `us_events = search(eventid='ci3144585', catalog='us')`
- Include Superseded Products: Superseded products are those that have been replaced by a product contributed from another center or by updated versions of the product. Including superseded products will also include all deleted products. This must be specified when using examining the [history of events](#History-Dataframe).
	- `ci3144585 = search(eventid='ci3144585', includesuperseded=True)`
- Include Deleted: This will allow deleted products **and** events to be included. This option is mutually exclusive to the 'includesuperseded`.
	- ci3144585 = search(eventid='ci3144585', includedeleted=True)`
- Host: By default the ComCat host is **earthquake.usgs.gov**, but this can be overriden using the host option.
	- `host_events = search(host='other_host')`
- Scenario: By default, libcomcat searches for real events. Use the --scenario option to search for scenario events.


## Classes
The three classes outlined in this section were designed to allow access to event information, products, and product contents.

See the [classes Jupyter notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/Classes.ipynb) for examples of these classes.

### SummaryEvent
The summary event object contains a short summary of an event and allows access to the detailed event object. Summary events can be accessed using the `search` method.

#### Summary Properties
The summary event's properties represent basic information about an event.
- alert: The alert level specified by PAGER. This can be green, yellow, orange, or red.
- depth: The depth of the earthquake defined by the authoritative origin.
- id: Earthquake ID from the authoritative origin.
- latitude: Earthquake latitude from the authoritative origin.
- longitude: Earthquake longitude from the authoritative origin.
- location: Earthquake location string.
- magnitude:  Earthquake magnitude from the authoritative origin.
- properties: The list of the event properties.
- time: Earthquake time from the authoritative origin.
- url: ComCat url associated with the event.

#### Summary Class Methods
- getDetailEvent: This method returns a DetailEvent object.
	- Parameters:
		- includedeleted: This will allow deleted products **and** events to be included. This option is mutually exclusive to the 'includesuperseded.
		- includesuperseded: Including superseded products will also include all deleted products. This must be specified when using examining the [history of events](#History-Dataframe).
- getDetailURL: Returns the url associated with the event.
- hasProduct: This tests to see whether a product exists for the event.
	- Parameters:
		- product: String representation of the product name.
- hasProperty: Tests to see if a property is in the list of properties. A property may not exist for all events. For example, properties acquired from the PAGER product, may not exist if there is no PAGER product for the event.
	- Parameters:
		- key: Property to check for.
- toDict: Returns the properties and their associated values as an ordered dictionary.
- []: The get item operator ([]) has been overloaded to return a property value, if the property is specified in the closed brackets.


### DetailEvent

The detail event object contains a more detailed summary of an event and allows access to the product object. Detailed events can be accessed using the `get_event_by_id` method or by using the summary event method, `getDetailEvent`.

#### Detail Properties
The detail event's properties are the **same as those of the summary event class** with the addition of:

- products: A list of the products available for the event.
- detail_url: The ComCat url that gives detailed event information in json format.

#### Detail Class Methods
`getDetailURL`, `hasProduct`, `hasProperty`, and `toDict` methods which are available for the summary event class are also available for the detail event. Additional class methods include:

- getNumVersions: This returns the number of versions available for a given product.
	- Parameters:
		- product_name: String representation of the product name.
- getProducts: This gets the product object(s) in the form of a list.
	- Parameters:
		- product_name: String representation of the product name.
		- source: Which source(s) contributed the product returned. Options include 'all', 'preferred', or any source network (e.g. 'us', 'ak'). Using the 'all' option will return product versions from every available source. 'preferred', which is the default will only return versions of products from one source.
		- version: Determines the version(s) returned. Options include 'preferred', 'first', 'last, 'all'.



### Product
The product object contains a summary of an event's product and allows access to the product's content files. Products can be accessed using the detail event method, `getProducts`.

#### Product Properties
Products have class properties that are consistent across all product types. However, properties also contain their own set of unique properties. This can be accessed using the product property, 'properties'.

- content: A list of the content files for the product.
- preferred_weight: The weight assigned to the product by ComCat.  This weight is defined when multiples of products are associated with an event.
- product_timestamp: The timestamp that defines the creation or submission time of the product. Standard protocol dictates that this timestamp should be defined by the network contributing the product. If this is not done, a timestamp is generated.
- properties: The list of properties specific to the product type.
- source: The source that contributed the product.
- version: The version of the product. ComCat does not generate a version number; as a result, the timestamp is used to generate a version number.


#### Product Class Methods
The `hasProperty` method which is available for the summary and detail event classes is also available for the product. Additional class methods include:

- getContent: Download a content file based on a file pattern.
	- Parameters:
		- regexp: The regular expression (pattern) that defines the file name. Since this method finds the shortest file name that matches the pattern, the longest pattern known should be used. For example, different file types may include the same file name (coulomb.inp or coulomb.mr). If 'coulomb' is the pattern used for the example files, then the 'coulomb.mr' file will be returned.
		- filename: The file name where the content file will be saved.
- getContentBytes: Returns a content file as bytes.
	- Parameters:
		- regexp: The regular expression (pattern), same as that of the getContent method.
- getContentsMatching: Returns a list of all files matching the file pattern.
	- Parameters:
		- regexp: File pattern to match.
- getContentName: This returns the name of the shortest file matching the file pattern.
	- Parameters:
		- regexp: File pattern to match.
- getContentURL: This returns ComCat url for the product content.
	- Parameters:
		- regexp: Content file pattern to match.

## Dataframes
Since there is such a large amount of information that can be accessed using the search methods and classes, significant information is organized in the form of pandas dataframes.

See the [dataframes Jupyter notebook](https://github.com/usgs/libcomcat/blob/master/notebooks/Dataframes.ipynb) for examples of these methods.


### Summary Dataframe
`from libcomcat.dataframes import get_summary_data_frame`

Summarizes basic information from a list of SummaryEvent objects.

The input is a list of summary event options. This can be acquired with the `search` method. The output is a dataframe with the following columns.
- id: Authoritative ComCat event ID.
- time: Authoritative event origin time.
 - latitude: Authoritative event latitude.
 - longitude: Authoritative event longitude.
 - depth: Authoritative event depth.
- magnitude : Authoritative event magnitude.

### Detail Dataframe
`from libcomcat.dataframes import get_detail_data_frame`

Summarizes more detailed information from a list of DetailEvent objects.

The parameters include:
- events: List of detail event objects. This can be acquired using the `get_event_by_id` method.
- get_all_magnitudes: A boolean that defines if magnitude information for each event should be stored in the dataframe. Default is False.
- get_tensors: Defines which tensors should be stored in the dataframe. Options include 'none', 'preferred', or 'all'. The default is 'preferred'.
- get_focals: Defines which focals should be stored in the dataframe. Options include 'none', 'preferred', or 'all'. The default is 'preferred'.
- get_moment_supplement: A boolean that defines if available origin and double-couple/source time information should be included in the dataframe.
- version: boolean that defines if the logging should included which information is found for each event. Default is False.

 The output is a dataframe with the following columns.
- id: Authoritative ComCat event ID.
- time: Authoritative event origin time.
 - latitude: Authoritative event latitude.
 - longitude: Authoritative event longitude.
 - depth: Authoritative event depth.
- magnitude : Authoritative event magnitude.
- location: Location description.
- magtype: The type of magnitude (e.g. mw, ml, mc).
- url: The ComCat url.
- alert: PAGER alert level
- ... additional columns depending on the chosen parameters.

### DYFI Dataframe
`from libcomcat.dataframes import get_dyfi_data_frame`

Creates a summary of 'Did You Feel It?' (DYFI) information.

The parameters include:
- detail: A detail event object. This can be acquired using the `get_event_by_id` method.
- dyfi_file: This indicates the resolution of the DYFI product. If this is not specified then the resolution will be picked from available resolutions in the order: utm_1km, utm_10km, utm_var, zip. The var option uses the best resolution for the map. The zip option uses a zip/city aggregated grid.
- version: The DYFI version. Options include 'none', 'preferred', or 'all'. The default is 'preferred'.

The output is a dataframe with the following columns.
- station: The station defined by the DYFI grid.
- lat: The latitude that defines the center of the station grid.
- lon The longitude that defines the center of the station grid.
- distance: The distance from the earthquake.
- intensity: The intensity derived from DYFI.
- nresp: The number of responses in the station grid.

### History Dataframe
`from libcomcat.dataframes import get_history_data_frame`

Creates a table detailing the history of an event's product(s).

The parameters include:
- detail: A detail event object. This can be acquired using the `get_event_by_id` method. **NOTE: The detail event must have been instantiated with include_superseded=True in order to be of interest. Otherwise only one version of each product will be available.**
- products: A list of products to examine. If no products are specified then all will be stored in the dataframe.


The output is a tuple with the dataframe with the following columns and the detailed event.
- Update Time: Time that the product was updated.
- Product: Product name.
- Authoritative Event ID: The authoritative event ID from ComCat.
- Code: The code for the event.
- Associated: Whether the product has been associated with the authoritative event.
- Product Source: The code for the network that contributed the source.
- Product Version: The version of the product derived from its timestamp.
- Elapsed (min): The time elapsed between the update time and the authoritative origin time.
- URL: The url that represents the version of the product.
- Comment: Comment associated with the product.
- Description: Information about the product, based upon the product's properties.



### PAGER Dataframe

`from libcomcat.dataframes import get_pager_data_frame`

Creates a table summarizing PAGER information for an event.

The parameters include:
- detail: A detail event object. This can be acquired using the `get_event_by_id` method.
- get_losses: A boolean defining if the fatalities, dollar losses, and uncertainties predicted should be included in the dataframe. Default is False.
- get_country_exposures: A boolean defining if the predicted exposures should be split by country. Default is False.
- get_all_versions: Gets the PAGER results for all versions of the PAGER product. Default is False.

The output is a dataframe with the following columns.
- id: Authoritative ComCat event ID.
- location: Description of the location.
- time: Authoritative event origin time.
 - latitude: Authoritative event latitude.
 - longitude: Authoritative event longitude.
 - depth: Authoritative event depth.
- magnitude : Authoritative event magnitude.
- country: The country corresponding to these exposures. If get_country_exposures is not set, then this will be the 'Total' exposures.
- pager_version: Version of PAGER used to generate the results.
- ... Exposures for each MMI intensity  (mmi1 - mmi10)
- ... Columns for containing loss information; if it is requested.

### Magnitude Dataframe

`from libcomcat.dataframes import get_magnitude_data_frame`

Creates a table summarizing station magnitude information for an event. This mimics the [magnitude sheet on the event page](https://earthquake.usgs.gov/earthquakes/eventpage/ci38996632/origin/magnitude).

The parameters include:
- detail: A detail event object. This can be acquired using the `get_event_by_id` method.
- catalog: The catalog that contributed. The default is 'preferred'.
- magtype: The type of magnitude (e.g. mb, ml, mc).

The output is a dataframe with the following columns.
- Channel: The code describing the network station in the format NETWORK.STATION.CHANNEL.LOCATION. '--' is a representation of missing information.
- Type: The type of magnitude.
- Amplitude: The amplitude of the wave at the station in meters.
- Period: The period of the wave at the station in seconds.
- Status: Whether it is manual or automatic.
- Magnitude: The magnitude derived locally for the station.
- Weight: The weight of the magnitude.


### Phase Dataframe

`from libcomcat.dataframes import get_phase_dataframe`

Creates a table summarizing the phase information for an event. This mimics the [phase sheet on the event page](https://earthquake.usgs.gov/earthquakes/eventpage/ci38996632/origin/phase).

The parameters include:
- detail: A detail event object. This can be acquired using the `get_event_by_id` method.
- catalog: The source network contributing phase information (e.g. ak, us). The default is 'preferred'.

The output is a dataframe with the following columns.
- Channel: The code describing the network station in the format NETWORK.STATION.CHANNEL.LOCATION. '--' is a representation of missing information.            
- Distance: The distance from the earthquake.
- Azimuth: Azimuth (degrees) from epicenter to station.
- Phase: The phase (e.g. Pn, PKPpre, etc.).
- Arrival Time: The UTC arrival time.
- Status: The status (automatic or manual).
- Residual: The calculated residual.
- Weight: The arrival time's weight.
- Agency: The id of the contributing agency.                
