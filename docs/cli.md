# Command Line Interface
----

Libcomcat provides a number of scripts that can be used to get summaries of information. This document details the purpose, the input parameters, and the outputs for each script.

## Contents
---
- [findid](#findid)
- [getcsv](#getcsv)
- [geteventhist](#geteventhist)
- [getmags](#getmags)
- [getpager](#getpager)
- [getphases](#getphases)
- [getproduct](#getproduct)
---

## findid
---
The `findid` script finds the id(s) of the closest earthquake to the input parameters. If an event id is known, this can be used to find the authoritative event id and the other ids associated with the event.

### Required Arguments

In order to search for ids some information must be provided. This can either be the location and time of the earthquake or an id.


| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
| -e, \-\-eventinfo | TIME LAT LON | Specify event information (TIME LAT LON). The time should be formatted as YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS. Latitude and longitude should be in decimal degrees. |  -e 2019-07-15T10:39:32 35.932 -117.715       |
|   -i, \-\-eventid       |      EVENTID  | Specify an event ID      |    -i  ci38572791    |

**Note:** These required arguments are mutually exclusive


### Optional Arguments
| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
| -a, \-\-all |  | Print all IDs associated with event, |  -a       |
|   -f, \-\-format   |      FORMAT  | Output format. Options include 'csv', 'tab', and 'excel'. Default is 'csv'.|    -f csv    |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
|   -o, \-\-outfile  |  FILE     | If the '-a' argument is used, send the output to a file. Denote the format using '-f'.|    -o eventids.csv|
|   -r, \-\-radius  |  RADIUS     | Change the search radius (km) around the specified latitude and longitude. Default is 100 km.|    \-\-radius 5|
|   -u, \-\-url  |       | Print the URL associated with event.|    \-\-url |
|   -v, \-\-verbose  |       | Print the time and distance deltas, and azimuth from input parameters to event.|    -v |
|   -w, \-\-window  |       | Change the window (sec) around the specified time. Default is 16 seconds.|    -w 20 |

* loglevel descriptions:
     - debug: Debugging message will be printed, most likely for developers.
              Most verbose.
     - info: Only informational messages, warnings, and errors will be printed.
     - warning: Only warnings (i.e., could not retrieve information for a
                single event out of many) and errors will be printed.
     - error: Only errors will be printed, after which program will stop.
              Least verbose

### Output
Depending on the optional parameters chosen, the output will either be information printed to the screen or a file. Specifying the '-a' with '-o FILE' will output a file (see example 5 and 6).

The output file appears as with the following columns:
- **id**: The event id.
- **time**: The event time.
- **latitude**: The event latitude.
- **longitude**: The event longitude.
- **depth**: The event depth.
- **magnitude**: The event magnitude.
- **distance(km)**: The distance (km) between this event and the input event.
- **timedelta(sec)**:  The time (sec) difference between this event and the input event.
- **azimuth(deg)**:  The azimuth from this event and the input event.
- **normalized_time_dist_vector**:  Creates a normalized vector from the time and distance difference information:


<img src="https://render.githubusercontent.com/render/math?math=v=\sqrt{(\frac{\Delta_t}{t_w})^2+(\frac{\Delta_x}{r})^2}">

where Delta_t is the time difference, Delta_x is the distance between events,
- **url**:  The azimuth from this event and the input event.



### Examples
1. To print the authoritative id of the event closest in time and space
inside a 100 km, 16 second window to "2019-07-15T10:39:32 35.932 -117.715":
`findid  -e 2019-07-15T10:39:32 35.932 -117.715`

2. To print the ComCat url of that nearest event:
`findid  -e 2019-07-15T10:39:32 35.932 -117.715 -u`

3. To print all of the events that are within expanded distance/time windows:
`findid  -e 2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120`

4. To find the authoritative and contributing ids:
`findid  -i ci38572791 -a -r 200 -w 120`

5. To write the output from the last command into a csv spreadsheet:
`findid  -e 2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120 -o temp.csv`

6. To write the output from the last command into an excel spreadsheet:
`findid  -e 2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120 -o temp.xls -f excel`

## getcsv
----
The `getcsv` script downloads basic earthquake information into a spreadsheet format.

### Required Arguments

A filename must be specified so that the information can be saved as a spreadsheet. The extension should be consistent with the output format chosen. **Note:** The default file format is comma delimited (csv).

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  |FILENAME|Output file name.| events.csv|

### Optional Arguments

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  \-\-alert-level | LEVEL |Limit to events with a specific PAGER alert level.*| \-\-alert-level yellow|
| -b, \-\-bounds|LONMIN LONMAX LATMIN LATMAX|Bounds to constrain event search [lonmin lonmax latmin latmax].|-b 163.213 -178.945 -48.980 -32.324|
| \-\-buffer|BUFFER|Use in conjunction with \-\-country. Specify a buffer (km) around the country's border where events will be selected.|\-\-buffer 5|
| -c, \-\-catalog|CATALOG|Source catalog from which products are derived (atlas, us, etc.).|-c atlas|
| \-\-contributor|CATALOG|Source contributor (who loaded product) (us, nc, etc.).| \-\-contributor ak|
| \-\-country|COUNTRY|Specify three character country code and earthquakes from inside country polygon (50m resolution) will be returned. Earthquakes in the ocean likely will NOT be returned. See https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes.| \-\-country ASM |
| -e, \-\-endtime|ENDTIME|End time for search (defaults to current date/time). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -e  2014-01-01 |
| -f, \-\-format|FORMAT|Output format (csv, tab, or excel). Default is 'csv'.| -f  excel |
| \-\-get-all-magnitudes||Extract all magnitudes (with sources), authoritative listed first.| \-\-get-all-magnitudes |
| \-\-get-moment-components||Extract preferred or all moment-tensor components (including type and derived hypocenter) where available.| \-\-get-moment-components |
| \-\-get-focal-angles||Extract preferred or all focal-mechanism angles (strike,dip,rake) where available.| \-\-get-focal-angles |
| \-\-get-moment-supplement||Extract moment tensor supplemental information (duration, derived origin, percent double couple) when available.| \-\-get-moment-supplement |
| \-\-host|HOST|Specify a different ComCat *search* host than earthquake.usgs.gov.| \-\-host |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
|  -m,  \-\-mag-range  |  MINMAG MAXMAG     |Minimum and maximum (authoritative) magnitude to restrict search.| -m 4 7|
|  \-\-sig-range  |  MINSIG MAXSIG     |Minimum and maximum significance values to restrict search.| \-\- sig-range 600 2000|
| \-\-numdays |  DAYS    |Number of days after start time (numdays and end-time options are mutually exclusive).| \-\-numdays 5|
| -p, \-\-product-type |  PRODUCT    |Limit the search to only those events containing products of type PRODUCT. See the full list here: https://usgs.github.io/pdl/userguide/products/index.html | -p shakemap|
| -r, \-\-radius |  RADIUS    |Search radius in kilometers (radius and bounding options are exclusive).| -r 5|
| -s, \-\-start-time |  START    |Start time for search (defaults to ~30 days ago). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -s 2013-01-01|
| -t, \-\-time-after |  TIME    |Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS.| -t 2015-01-01|
| \-\-version|      |Version of libcomcat.| \-\-version |
| -x, \-\-count|      |Just return the number of events in search and maximum allowed.| -x |

* alert-level descriptions
	- green; Limit to events with PAGER alert level "green".
    - yellow; Limit to events with PAGER alert level "yellow".
	- orange; Limit to events with PAGER alert level "orange".
	- red; Limit to events with PAGER alert level "red"

### Output
The output file appears as with the following columns:
- **id**: The event id.
- **time**: The event time.
- **latitude**: The event latitude.
- **longitude**: The event longitude.
- **depth**: The event depth.
- **magnitude**: The event magnitude.
- **alert**: The event alert level.
- **url**: Event url.

**Note:** Depending on the optional parameters included additional columns related to magnitude, focal, or tensor information will be included.


### Examples
1. To download basic event information (time, lat, lon, depth, magnitude) and moment tensor components for a box around New Zealand during 2013:
`getcsv nz.csv -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f csv`

2. To expand the results to include preferred moment tensors:
`getcsv nz.xlsx --get-moment-components preferred -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f excel`

3. To expand the results to include ALL moment tensors:
`getcsv nz.xlsx --get-moment-components all -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f excel`

4. To expand the results to include preferred focal mechanisms:
`getcsv nz.xlsx --get-focal-angles preferred -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f excel`

5. To expand the results to include ALL focal mechanisms:
`getcsv nz.xlsx --get-focal-angles all -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f excel`

6. To include all magnitudes (including source and type) for that same search, add the -g flag:
`getcsv nz.csv --get-moment-components -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 --get-all-magnitudes -f csv`

7. To print (to the screen) the number of events that would be returned from the above query, and the maximum number of events supported by ONE ComCat query*:
`getcsv tmp.csv -x --get-moment-components -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01`

8. To download events with fractional days, use the ISO 8601 combined date time format (YYYY-mm-ddTHH:MM:SS, YYYY-mm-ddTHH:MM:SS.s):
`getcsv tmp.csv -s 2015-01-01T00:00:00 -e 2015-01-01T01:15:00 -b -180 180 -90 90`


## geteventhist
---
The `geteventhist` script summarizes the history of event products.

### Required Arguments

An event id must be specified.

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  |EVENTID  | Specify an event ID.      |    ci38572791    |

### Optional Arguments

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  -d, \-\-outdir | DIRECTORY |Directory where files are stored.| -d .|
|  \-\-exclude-products | EXCLUDE |ComCat products to be excluded from the spreadsheet.| \-\-exclude-products dyfi|
|   -f, \-\-format   |      FORMAT  | Output format. Options include 'csv', 'tab', and 'excel'. Default is 'csv'.|    -f csv    |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
| -p, \-\-product-type |  PRODUCT    |Limit to only the products specified. If no products are specified, all will be listed. See the full list of products here: See the full list here: https://usgs.github.io/pdl/userguide/products/index.html.| -p shakemap|
|   -r, \-\-radius  |  RADIUS     | Search for other unassociated earthquakes  inside a search radius (km) (Requires use of -w.)|    \-\-radius 5|
|   \-\-split  |       |  Split descriptions of single-product queries into separate columns. |    \-\-split|
| \-\-version|      |Version of libcomcat.| \-\-version |
| \-\-web|      |Print HTML tables to stdout.| \-\-web |
| -w, \-\-window|   WINDOW   |Limit by time window in seconds. (Requires use of -r.)| -w 30 |

### Output
Depending on the optional parameters chosen, the output will either be information printed to the screen (\-\-web) or a file.

The output file appears as with the following columns:
- **id**: The event id.
- **time**: The event time.
- **latitude**: The event latitude.
- **longitude**: The event longitude.
- **depth**: The event depth.
- **magnitude**: The event magnitude.
- **alert**: The event alert level.
- **url**: Event url.

**Note:** Depending on the optional parameters included additional columns related to magnitude, focal, or tensor information will be included.


### Examples
To get one summary spreadsheet in Excel format listing all products for the M7.1 event from the 2019 Ridgecrest Sequence:
`geteventhist ci38457511 -d ~/tmp/ridgecrest -f excel`

To get one summary spreadhsheet as above, *excluding* DYFI products:
`geteventhist ci38457511 -d ~/tmp/ridgecrest -f excel --exclude-products dyfi`

To split out the "description" column into separate columns, and the products into separate spreadsheets:
`geteventhist ci38457511 -d ~/tmp/ridgecrest -f excel --split`

To retrieve summary information for only origins and shakemaps:
`geteventhist ci38457511 -d ~/tmp/ridgecrest -f excel -p origin shakemap`

To retrieve information for only origins and shakemaps, and split them into separate spreadsheets:
`geteventhist ci38457511 -d ~/tmp/ridgecrest -f excel -p origin shakemap --split`

To print one product table (say, origins) to stdout in HTML format:
`geteventhist ci38996632  -p origin --web --split > ~/test.html`

## getmags
---

The `getmags` script summarizes epicenter and magnitude information.

### Required Arguments


A filename must be specified so that the information can be saved as a spreadsheet. The extension should be consistent with the output format chosen. **Note:** The default file format is comma delimited (csv).

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  |FILENAME|Output file name.| events.csv|

### Optional Arguments

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
| -b, \-\-bounds|LONMIN LONMAX LATMIN LATMAX|Bounds to constrain event search [lonmin lonmax latmin latmax].|-b 163.213 -178.945 -48.980 -32.324|
| -e, \-\-endtime|ENDTIME|End time for search (defaults to current date/time). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -e  2014-01-01 |
| -f, \-\-format|FORMAT|Output format (csv, tab, or excel). Default is 'csv'.| -f  excel |
| \-\-get-all-magnitudes||Extract all magnitudes (with sources), authoritative listed first.| \-\-get-all-magnitudes |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
|  -m,  \-\-mag-range  |  MINMAG MAXMAG     |Minimum and maximum (authoritative) magnitude to restrict search.| -m 4 7|
| -r, \-\-radius |  LAT LON RADIUS    |Search radius in kilometers (radius and bounding options are mutually exclusive). The latitude and longitude for the search should be specified before the radius.| -r -48.980 -178.945 10|
| -s, \-\-start-time |  START    |Start time for search (defaults to ~30 days ago). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -s 2013-01-01|
| -t, \-\-time-after |  TIME    |Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS.| -t 2015-01-01|
| \-\-version|      |Version of libcomcat.| \-\-version |
| -x, \-\-count|      |Just return the number of events in search and maximum allowed.| -x |



### Output
The output file appears with the following columns:
- **id**: The event id.
- **time**: The event time.
- **lat**: The event latitude.
- **lon**: The event longitude.
- **depth**: The event depth.
- **location**: Event location string.
- **url**: Event url.
- **hypo_src**: Source that contributed the hypocenter.
- **SOURCE_MAGNITUDETYPE**:  The magnitude (of a specific type) for a denoted source

**Note:** The last column description (SOURCE_MAGNITUDETYPE) represents many columns. A column will be added for every contributing source and every magnitude type that the source contributed.


### Examples
Download epicenter and all contributed magnitudes in line format (csv, tab, etc.):
`getmags nz.csv -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f csv`

To download events with fractional days, use the ISO 8601 combined date time format (YYYY-mm-ddTHH:MM:SS, YYYY-mm-ddTHH:MM:SS.s):
`getmags recent.csv 2015-01-01T00:00:00 -e 2015-01-01T01:15:00`

## getpager
---
The `getpager` script summarizes estimated exposures and losses for events.

### Required Arguments


A filename must be specified so that the information can be saved as a spreadsheet. The extension should be consistent with the output format chosen. **Note:** The default file format is comma delimited (csv).

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  |FILENAME|Output file name.| events.csv|

### Optional Arguments

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
| -a, \-\-all| |Retrieve information from all versions of PAGER.|-a|
| -b, \-\-bounds|LONMIN LONMAX LATMIN LATMAX|Bounds to constrain event search [lonmin lonmax latmin latmax].|-b 163.213 -178.945 -48.980 -32.324|
| -e, \-\-endtime|ENDTIME|End time for search (defaults to current date/time). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -e  2014-01-01 |
| -f, \-\-format|FORMAT|Output format (csv, tab, or excel). Default is 'csv'.| -f  excel |
| \-\-get-countries||Retrieve information from all countries affected by the earthquake.| \-\-get-countries |
| \-\-get-losses||Retrieve fatalities and economic losses.| \-\-get-losses |
| \-\-host|HOST|Specify a different ComCat *search* host than earthquake.usgs.gov.| \-\-host |
|   -i, \-\-eventid       |      EVENTID  | Specify an event ID      |    -i  ci38572791    |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
|  -m,  \-\-mag-range  |  MINMAG MAXMAG     |Minimum and maximum (authoritative) magnitude to restrict search.| -m 4 7|
| -r, \-\-radius |  LAT LON RADIUS    |Search radius in kilometers (radius and bounding options are mutually exclusive). The latitude and longitude for the search should be specified before the radius.| -r -48.980 -178.945 10|
| -s, \-\-start-time |  START    |Start time for search (defaults to ~30 days ago). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -s 2013-01-01|
| -t, \-\-time-after |  TIME    |Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS.| -t 2015-01-01|
| \-\-version|      |Version of libcomcat.| \-\-version |


### Output
The output file appears as with the following columns:
- **id**: The event id.
- **location**: Event location string.
- **time**: The event time.
- **latitude**: The event latitude.
- **longitude**: The event longitude.
- **depth**: The event depth.
- **magnitude**: The event magnitude.
- **country**: Country associated with the mmi exposures (will be "Total" only if \-\-get-countries is not specified).
- **pager_version**: Version of pager.
- **mmi1**: Predicted population exposed to MMI1 shaking.
- **mmi2**: Predicted population exposed to MMI2 shaking.
- **mmi3**: Predicted population exposed to MMI3 shaking.
- **mmi4**: Predicted population exposed to MMI4 shaking.
- **mmi5**: Predicted population exposed to MMI5 shaking.
- **mmi6**: Predicted population exposed to MMI6 shaking.
- **mmi7**: Predicted population exposed to MMI7 shaking.
- **mmi8**: Predicted population exposed to MMI8 shaking.
- **mmi9**: Predicted population exposed to MMI9 shaking.
- **mmi10**: Predicted population exposed to MMI10 shaking.
If \-\-get-losses is specified the following columns are appended
- **predicted_fatalities**: The result of applying loss models to the exposure data. (Not guaranteed to match the actual fatalities caused by the event.)
- **fatality_sigma**: Calculated sigma value for the fatalities loss value and G statistic.
- **predicted_dollars**: The result of applying loss models to the exposure data. (Not guaranteed to match the actual fatalities caused by the event.)
- **dollars_sigma**: Calculated sigma value for the monetary loss value and G statistic.

### Examples
Get total exposures:
`getpager nz.csv -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f csv`

Separate country exposures:
`getpager nz.csv -b 163.213 -178.945 -48.980 -32.324 -s 2018-01-02 -e 2019-10-30 -f csv --get-countries`

Get fatalities and monetary losses:
`getpager nz.csv -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01 -f csv --get-losses`

## getphases
---

The `getphases` script outputs a spreadsheet of basic earthquake information and phase information.

### Required Arguments

A directory must be specified so that the information can be saved to a folder. The directory must exist before the script is executed.

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  |DIRECTORY|Output directory.| .|

### Optional Arguments

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
| -b, \-\-bounds|LONMIN LONMAX LATMIN LATMAX|Bounds to constrain event search [lonmin lonmax latmin latmax].|-b 163.213 -178.945 -48.980 -32.324|
| -c, \-\-catalog|CATALOG|Source catalog from which products are derived (atlas, us, etc.).|-c atlas|
| \-\-contributor|CONTRIBUTOR|Source contributor (who loaded product) (us, nc, etc.).| \-\-contributor ak|
| -e, \-\-endtime|ENDTIME|End time for search (defaults to current date/time). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -e  2014-01-01 |
| -f, \-\-format|FORMAT|Output format (csv, tab, or excel). Default is 'csv'.| -f  excel |
|   -i, \-\-eventid       |      EVENTID  | Specify an event ID      |    -i  ci38572791    |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
|  -m,  \-\-mag-range  |  MINMAG MAXMAG     |Minimum and maximum (authoritative) magnitude to restrict search.| -m 4 7|
| -r, \-\-radius |  LAT LON RADIUS    |Search radius in kilometers (radius and bounding options are mutually exclusive). The latitude and longitude for the search should be specified before the radius.| -r -48.980 -178.945 10|
| -s, \-\-start-time |  START    |Start time for search (defaults to ~30 days ago). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -s 2013-01-01|
| -t, \-\-time-after |  TIME    |Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS.| -t 2015-01-01|
| \-\-version|      |Version of libcomcat.| \-\-version |


### Output
One file will be saved for each event.

The output file appears as with the following columns:
- **Channel**: Network.Station.Channel.Location (NSCL) style station description. ("--" indicates missing information)
- **Distance**: Distance (kilometers) from epicenter to station.
- **Azimuth**: Azimuth (degrees) from epicenter to station.
- **Phase**: Name of the phase (Pn,Pg, etc.)
- **Arrival Time**: Pick arrival time (UTC).
- **Status**: "manual" or "automatic".
- **Residual**: Arrival time residual.
- **Weight**: Arrival weight.
- **Agency**: Agency that contributed the information.

### Examples
To download phase data to Excel format for a small rectangle in Oklahoma in 2017:
`getphases ~/tmp/phase_data -b -97.573 -97.460 36.247 36.329 -s 2017-08-26 -e 2017-09-15 -f excel`

To download phase data for the 2017 7.1 Mexico City event:
`getphases ~/tmp/phase_data -i us2000ar20 -f excel`


## getproduct
---


The `getproduct` script downloads product content files.

### Required Arguments

The product and content file(s) requested must be specified. The shortest content file name will be matched with the input content file pattern. For example if us2000ar20_coulomb.inp and us2000ar20.png are content files for a product, using 'coulomb.inp' as the content file pattern will match to us2000ar20_coulomb.inp.

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
|  |PRODUCT|Name of the desired product. See the full list here: https://usgs.github.io/pdl/userguide/products/index.html.| finite-fault |
|  |[CONTENTS]|The names of the product contents (grid.xml, stationlist.txt, etc.).| .inp .mr |

### Optional Arguments

| Argument(s)     | Expected Argument(s)    | Description | Example |
|-----------------|-------------------------|-------------|---------|
| -b, \-\-bounds|LONMIN LONMAX LATMIN LATMAX|Bounds to constrain event search [lonmin lonmax latmin latmax].|-b 163.213 -178.945 -48.980 -32.324|
| \-\-buffer|BUFFER|Use in conjunction with \-\-country. Specify a buffer (km) around the country's border where events will be selected.|\-\-buffer 5|
| -c, \-\-catalog|CATALOG|Source catalog from which products are derived (atlas, us, etc.).|-c atlas|
| \-\-contributor|CONTRIBUTOR|Source contributor (who loaded product) (us, nc, etc.).| \-\-contributor ak|
| \-\-country|COUNTRY|Specify three character country code and earthquakes from inside country polygon (50m resolution) will be returned. Earthquakes in the ocean likely will NOT be returned. See https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes. **Note:** This only works for Linux and Unix OS.| \-\-country ASM |
|  -d, \-\-outdir | DIRECTORY |Directory where files are stored.| -d .|
| -e, \-\-endtime|ENDTIME|End time for search (defaults to current date/time). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -e  2014-01-01 |
| \-\-event-property |PROPERTY|Event property. | \-\-event-property  status:REVIEWED |
| \-\-event-type |TYPE|Event type. | \-\-event-type  earthquake |
| \-\-get-source |SOURCE|Get contents for the "preferred" source, "all" sources, or a specific source. | \-\-get-source us |
| \-\-get-version |VERSION|Get contents for first, last, preferred or all versions of product. Default is preferred.| \-\-get-version all |
| \-\-scenario||Retrieve data from ComCat Scenario Server.| \-\-scenario |
| \-\-host|HOST|Specify a different ComCat *search* host than earthquake.usgs.gov.| \-\-host |
|   -i, \-\-eventid       |      EVENTID  | Specify an event ID      |    -i  ci38572791    |
|   -l, \-\-list-url       |        |Only list urls for contents in events that match criteria.     |    -l |
|   \-\-logfile  |       |Send debugging, informational, warning and error messages to a file.|    \-\-logfile   |
|   \-\-loglevel  |  LEVEL     |Set the minimum logging level. Options include 'debug', 'info', 'warning', and 'error'.*|    \-\-loglevel debug|
|  -m,  \-\-mag-range  |  MINMAG MAXMAG     |Minimum and maximum (authoritative) magnitude to restrict search.| -m 4 7|
| -r, \-\-radius |  LAT LON RADIUS    |Search radius in kilometers (radius and bounding options are mutually exclusive). The latitude and longitude for the search should be specified before the radius.| -r -48.980 -178.945 10|
| -s, \-\-start-time |  START    |Start time for search (defaults to ~30 days ago). YYYY-mm-dd, YYYY-mm-ddTHH:MM:SS, or YYYY-mm-ddTHH:MM:SS.s.| -s 2013-01-01|
| -t, \-\-time-after |  TIME    |Limit to events after specified time. YYYY-mm-dd or YYYY-mm-ddTHH:MM:SS.| -t 2015-01-01|
| \-\-version|      |Version of libcomcat.| \-\-version |


### Output
One file will be saved for each event depends on the product and content files specified.

### Examples
To download ShakeMap grid.xml files for a box around New Zealand during 2013:
`getproduct shakemap "grid.xml" -d /home/user/newzealand -b 163.213 -178.945 -48.980 -32.324 -s 2013-01-01 -e 2014-01-01`

To retrieve all of the coulomb input files for the finite-fault product, you would construct your search like this:
`getproduct finite-fault .inp -d ~/tmp/chile -b -76.509 -49.804  -67.72 -17.427 -s 2007-01-01 -e 2016-05-01 -m 6.5 9.9`

To retrieve the moment rate function files, do this:
`getproduct finite-fault .mr -d ~/tmp/chile -b -76.509 -49.804  -67.72 -17.427 -s 2007-01-01 -e 2016-05-01 -m 6.5 9.9`

    ################################################################################################################################
    Scenarios: The USGS National Earthquake Information Center generates
    scenario (that is, not real) earthquakes for use in planning
    emergency response, training, investigations of possible
    vulnerabilities in structures, etc. These scenarios contain
    ShakeMap products (maps, data file) which can be downloaded from the
    Scenario server.

    These scenarios can be found on the web here:

    https://earthquake.usgs.gov/scenarios/

    Note that these are not earthquakes that *have* happened, nor are
    they earthquakes that *will* happen. In many cases, the parameters
    for these scenarios are chosen to generate a worst case but possible
    earthquake, and not necessarily a *likely* earthquake.

    To retrieve SCENARIO shakemap intensity.jpg files in Northern California
    (note that scenario origin times are pretty meaningless):

    %(prog)s shakemap-scenario intensity.jpg -b -123 -119 35 40 -s 2013-10-01 -e 2013-10-30 -m 0.0 9.9 --scenario -d ~/tmp/scenario
    ################################################################################################################################
