function [event,table] = read_phases(filename)
% read_phases  Read event and phase data from CSV files created by libcomcat getphases program.
%
% libcomcat is a set of tools available on GitHub for downloading various
% types of data from the USGS earthquake Comprehensive Catalog, or ComCat.
% getphases is one of those tools, and is documented here:
%
% http://usgs.github.io/libcomcat/programs/getphases.html
%
%   (at command line) getphases . -i us2000b3dm --format=csv
%   [event,phases] = read_phases('./us2000b3dm_phases.csv') returns an
%   event structure, which consists of the following fields:
%    - id: USGS authoritative ComCat ID.
%    - time: Matlab datenum representing origin time.
%    - location: String describing location of the earthquake.
%    - latitude: Origin latitude.
%    - longitude: Origin longitude.
%    - depth: Origin depth.
%    - magnitude: Event magnitude.
%    - magtype: Magnitude type.
%    - url: ComCat URL where earthquake information can be found.
%    - Any remaining fields will contain moment tensor data, if available.
%      These fields will be preceded by moment tensor source and method.
%      For example, a moment tensor created by the NEIC using the W-phase
%      algorithm will have the following fields:
%      - us_Mww_mrr: Mrr moment tensor component.
%      - us_Mww_mtt: Mtt moment tensor component.
%      - us_Mww_mpp: Mpp moment tensor component.
%      - us_Mww_mrt: Mrt moment tensor component.
%      - us_Mww_mrp: Mrp moment tensor component.
%      - us_Mww_mtp: Mtp moment tensor component.
%      - us_Mww_np1_strike: Strike of the first nodal plane.
%      - us_Mww_np1_dip: Dip of the first nodal plane.
%      - us_Mww_np1_rake: Rake of the first nodal plane.
%      - us_Mww_np2_strike: Strike of the second nodal plane.
%      - us_Mww_np2_dip: Dip of the second nodal plane.
%      - us_Mww_np2_rake: Rake of the second nodal plane.
% 
%   and a Matlab table object, where rows consist of phase data
%   and columns are the following:
%    - Channel Network.Station.Channel.Location (NSCL) style station description.
%      ( '-'  indicates missing information)
%    - Distance Distance (kilometers) from epicenter to station.
%    - Azimuth Azimuth (degrees) from epicenter to station.
%    - Phase Name of the phase (Pn,Pg, etc.)
%    - ArrivalTime Pick arrival time (UTC).
%    - Status 'manual' or 'automatic'.
%    - Residual Arrival time residual.
%    - Weight Arrival weight.

    opts = detectImportOptions(filename,'CommentStyle','#','Delimiter',',');
    if isa(opts,'matlab.io.spreadsheet.SpreadsheetImportOptions')
        msgID = 'read_phases:inputError';
        msgtext = 'Excel files are not supported by read_phases function.';
        throw(MException(msgID,msgtext));
    else
        table = readtable(filename,'CommentStyle','#','Delimiter',',');
    end
    fid = fopen(filename,'r');
    tline = fgetl(fid);
    event = struct();
    while tline(1) == '#'
        if tline(2) == '%'
            tline = fgetl(fid);
            continue
        end
        parts = regexp(tline(2:end),'=','split');
        key = strtrim(parts{1});
        value = strtrim(parts{2});
        if strcmp(key,'time')
            value = datenum(value);
        elseif length(str2num(value))
            value = str2num(value);
        end
        event = setfield(event,key,value);
        tline = fgetl(fid);
    end
    fclose(fid);
