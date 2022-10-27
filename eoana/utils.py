# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-12-11 15:57

@author: johannes

"""
import os
import math
import numpy as np
from collections import Mapping
from shapely.geometry import Polygon, Point
from datetime import datetime
from pyproj import CRS, transform
from decimal import Decimal, ROUND_HALF_UP
from functools import reduce


class BitFlags:
    """Manipulate flags stored bitwise."""

    def __init__(self, masks, meanings):
        """Init the flags."""
        self._masks = masks
        self._meanings = meanings
        self._map = dict(zip(meanings, masks))

    def match_item(self, item, data):
        """Match any of the item."""
        mask = self._map[item]
        return np.bitwise_and(data, mask).astype(np.bool)

    def match_any(self, items, data):
        """Match any of the items in data."""
        mask = reduce(np.bitwise_or, [self._map[item] for item in items])
        return np.bitwise_and(data, mask).astype(np.bool)

    def __eq__(self, other):
        """Check equality."""
        return all(self._masks == other._masks) and self._meanings == other._meanings


def get_mask(satpy_scn):
    """Doc."""
    bflags = BitFlags(satpy_scn['wqsf'].attrs['flag_masks'],
                      satpy_scn['wqsf'].attrs['flag_meanings'].split())

    return bflags.match_any(["INVALID", "SNOW_ICE", "INLAND_WATER", "SUSPECT",
                             "AC_FAIL", "CLOUD", "HISOLZEN", "CLOUD_MARGIN",
                             "CLOUD_AMBIGUOUS", "LOWRW", "LAND"],
                            satpy_scn['wqsf'])


def get_polygon(llc=None, urc=None, coord_list=None):
    if coord_list:
        pointlist = [Point(math.degrees(c.lon), math.degrees(c.lat)) for c in coord_list]
    else:
        pointlist = [
            Point(llc),
            Point(urc[0], llc[1]),
            Point(urc),
            Point(llc[0], urc[1])
        ]
    return Polygon([[p.x, p.y] for p in pointlist])


def decmin_to_decdeg(pos, string_type=True, decimals=4):
    """
    :param pos: str, Position in format DDMM.mm (Degrees + decimal minutes)
    :param string_type: As str?
    :param decimals: Number of decimals
    :return: Position in format DD.dddd (Decimal degrees)
    """
    pos = float(pos)

    output = np.floor(pos/100.) + (pos % 100)/60.
    output = round_value(output, nr_decimals=decimals)
    # output = "%.5f" % output
    if string_type:
        return output
    else:
        return float(output)


def decdeg_to_decmin(pos: (str, float), string_type=True, decimals=2) -> (str, float):
    """
    :param pos: Position in format DD.dddd (Decimal degrees)
    :param string_type: As str?
    :param decimals: Number of decimals
    :return: Position in format DDMM.mm(Degrees + decimal minutes)
    """
    pos = float(pos)
    deg = np.floor(pos)
    minute = pos % deg * 60.0
    if string_type:
        if decimals:
            output = ('%%2.%sf'.zfill(7) % decimals % (float(deg) * 100.0 + minute))
        else:
            output = (str(deg * 100.0 + minute))

        if output.index('.') == 3:
            output = '0' + output
    else:
        output = (deg * 100.0 + minute)
    return output


def generate_filepaths(directory: str, pattern=''):
    """
    :param directory: str, directory path
    :param pattern: str
    :return: generator
    """
    for path, subdir, fids in os.walk(directory):
        for f in fids:
            if pattern in f:
                yield os.path.abspath(os.path.join(path, f))


def generate_folder_paths(directory: str, pattern=''):
    """Doc."""
    for path, subdir, fids in os.walk(directory):
        for f in fids:
            if pattern in subdir:
                yield os.path.abspath(os.path.join(path, f))


def get_now_time(fmt=None) -> str:
    """
    :param fmt: str, format to export datetime object
    :return:
    """
    fmt = fmt or '%Y-%m-%d %H:%M:%S'
    return datetime.now().strftime(fmt)


def get_idx(lat_array, lon_array, lat, lon):
    """Return grid-index for closest position based on the given lat and lon."""
    new_lat_mat = abs(lat_array - lat)
    new_lon_mat = abs(lon_array - lon)
    pos_in_mat = new_lat_mat + new_lon_mat
    # i = np.where(pos_in_mat == pos_in_mat.min())  # return: (array(idx_X), array(idx_Y))
    i = np.unravel_index(pos_in_mat.argmin(), pos_in_mat.shape)
    # print(i)
    if len(i) > 2:
        print('Multiple position combination.. NOT GOOD')

    return i


def recursive_dict_update(d: dict, u: dict) -> dict:
    """ Recursive dictionary update using
    Copied from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        via satpy
    """
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = recursive_dict_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def round_value(value: (str, int, float), nr_decimals=2) -> str:
    """"""
    return str(Decimal(str(value)).quantize(Decimal('%%1.%sf' % nr_decimals % 1), rounding=ROUND_HALF_UP))


def transform_ref_system(lat=None, lon=None, in_proj='EPSG:3006', out_proj='EPSG:4326'):
    """
    Transform coordinates from one spatial reference system to another.
    in_proj is your current reference system
    out_proj is the reference system you want to transform to, default is EPSG:4326 = WGS84
    (Another good is EPSG:4258 = ETRS89 (Europe), almost the same as WGS84 (in Europe)
    and not always clear if coordinates are in WGS84 or ETRS89, but differs <1m.
    lat = latitude
    lon = longitude
    To find your EPSG check this website: http://spatialreference.org/ref/epsg/
    """
    o_proj = CRS(out_proj)
    i_proj = CRS(in_proj)

    x, y = transform(i_proj, o_proj, float(lon), float(lat), always_xy=True)

    return y, x
