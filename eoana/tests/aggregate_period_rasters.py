#!/usr/bin/env python3
"""
Created on 2022-04-27 14:14

@author: johannes
"""
import os
import numpy as np
import pandas as pd
import rasterio as rio
from itertools import chain


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


def write_raster(path, data, meta):
    with rio.open(path, 'w', **meta) as out:
        out.write(data, 1)
    out.close()


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


def get_sat_path(*args):
    """Get path to sat-BAWS-data."""
    files = ()
    for p in args:
        generator = generate_filepaths(
            r'C:\Temp\Satellit\olci_output\helcom_daily_mean',
            pattern=p
        )
        files = chain(files, generator)
    return files


if __name__ == '__main__':
    rst2 = rio.open(r'C:\Utveckling\eoana\eoana\etc\basin_grid\raster_template_baws300_sweref99tm.tiff')
    out_path = r'C:\Temp\Satellit\olci_output\period_mean\{}.tiff'
    meta = {m: rst2.meta[m] for m in ('driver', 'dtype', 'nodata', 'width', 'height', 'count', 'transform')}
    meta['dtype'] = 'float32'
    meta['count'] = 1
    meta['compress'] = 'lzw'

    periods = {
        'spring': ('03', '04', '05'),
        'summer': ('06', '07', '08'),
        'autumn': ('09', '10', '11'),
    }
    for year in range(2017, 2022):
        print(year)
        if year != 2021:
            continue
        for mon in ('06', '07', '08'):
            print(mon)
            if mon != '07':
                continue
            files = get_sat_path(f'{year}{mon}')
            mean_array = get_daily_mean(files)
            if not mean_array.size:
                continue
            write_raster(
                out_path.format(f'{year}_{mon}'),
                np.round(np.power(10, mean_array), 4),
                # mean_array,
                meta
            )
        # for period, months in periods.items():
        #     print(period)
        #     files = get_sat_path(*(f'{year}{p}' for p in months))
        #     mean_array = get_daily_mean(files)
        #     if not mean_array.size:
        #         continue
        #     write_raster(
        #         out_path.format(f'{year}_{period}'),
        #         # np.round(np.power(10, mean_array), 4),
        #         mean_array,
        #         meta
        #     )
