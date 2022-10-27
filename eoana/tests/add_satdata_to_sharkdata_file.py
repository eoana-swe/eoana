#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-04-26 16:08

@author: johannes
"""
import os
import json
import numpy as np
import pandas as pd
import rasterio as rio
import warnings
warnings.filterwarnings('ignore')


def generate_filepaths(directory: str, pattern=''):
    """Generate file paths."""
    for path, _, fids in os.walk(directory):
        for f in fids:
            if pattern in f:
                yield os.path.abspath(os.path.join(path, f))


def get_array_from_raster(path):
    rst = rio.open(path)
    array = rst.read()
    return array[0]


def get_daily_mean(daily_files):
    daily_passages = []
    for fid in daily_files:
        data = get_array_from_raster(fid)
        data = np.where(data == 0, np.nan, data)
        daily_passages.append(data)

    if not daily_passages:
        return np.array(())
    else:
        return np.nanmean(daily_passages, axis=0)


def get_sat_path(sdate):
    """Get path to sat-BAWS-data."""
    generator = generate_filepaths(
        r'C:\Temp\Satellit\olci_output\helcom',
        pattern=sdate
    )
    return generator


def get_timestamp(*args):
    return pd.Timestamp(' '.join(args))


if __name__ == '__main__':

    with open(r'position_index.json', 'r') as fd:
        position_indices = json.load(fd)
    fd.close()

    data = pd.read_csv(
        r'sharkweb_data_all_chl_2016-2021_incl_helcom_basins.txt',
        header=0,
        sep='\t',
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )
    data['timestamp'] = data[['SDATE', 'STIME']].apply(
        lambda x: get_timestamp(*x), axis=1)
    data['pos_string'] = data[['LATIT_DD', 'LONGI_DD']].apply(
        lambda x: '-'.join(x),
        axis=1
    )
    data['CHL_NN'] = np.nan
    data['CHL_NN_3x3'] = np.nan
    data = data.sort_values(by='timestamp').reset_index(drop=True)

    for date in data['SDATE'].unique():
        files = get_sat_path(date.replace('-', ''))
        mean_array = get_daily_mean(files)
        if not mean_array.size:
            continue

        print(date)

        boolean_date = data['SDATE'] == date
        for row in data[boolean_date].itertuples():
            grid_index = tuple(position_indices.get(row.pos_string))
            if grid_index:
                data['CHL_NN'][row.Index] = np.power(10, mean_array[grid_index])
                xi, yi = grid_index
                data['CHL_NN_3x3'][row.Index] = np.power(
                    10, np.nanmean(mean_array[xi - 1: xi + 2, yi - 1: yi + 2])
                )
    data.to_csv(
        r'sharkweb_data_all_chl_2016-2021_incl_helcom_basins_chl_nn_ver003.txt',
        header=True,
        sep='\t',
        index=None,
        encoding='cp1252',
    )
