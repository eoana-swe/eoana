# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-03-24 09:13
@author: johannes
"""
import time
import numpy as np
import rasterio as rio
import matplotlib.pyplot as plt
import xarray as xr


class GeoTIFFReader:
    """
    """
    @staticmethod
    def read(fid, as_type=None, nan_value=None):
        as_type = as_type or float
        nan_value = nan_value or 255.
        rst = rio.open(fid)
        array = rst.read()
        array = array[0].astype(as_type)
        array = np.where(array == nan_value, np.nan, array)
        return array

    @staticmethod
    def read_meta(fid):
        rst = rio.open(fid)
        meta = rst.meta.copy()
        meta.update(compress='lzw')
        return meta


def xarray_reader(fid):
    xarr = xr.open_rasterio(fid)
    # xarr.sizes['x']
    # xarr.sizes['y']
    # xarr.coords['x'].data
    # xarr.coords['y'].data
    # xarr.data


if __name__ == "__main__":
    fid = 'C:/Temp/Satellit/sentinel_data/kubdata/2021-02-26-.tif'
    gf_reader = GeoTIFFReader()
    array = gf_reader.read(fid, as_type=float)
    meta = gf_reader.read_meta(fid)
