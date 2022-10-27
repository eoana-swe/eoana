#!/usr/bin/env python3
"""
Created on 2022-04-27 14:14

@author: johannes
"""
import os
import numpy as np
import pandas as pd
import rasterio as rio


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


def get_sat_path(sdate):
    """Get path to sat-BAWS-data."""
    generator = generate_filepaths(
        r'C:\Temp\Satellit\olci_output\helcom',
        pattern=sdate
    )
    return generator


if __name__ == '__main__':
    """
    Aggregate daily satellite passages in order to make one file per date.
    """
    rst = rio.open(r'C:\Utveckling\eoana\eoana\etc\basin_grid\raster_template_baws300_sweref99tm.tiff')
    out_path = r'C:\Temp\Satellit\olci_output\helcom_daily_mean\{}.tiff'
    meta = {m: rst.meta[m] for m in ('driver', 'dtype', 'nodata', 'width', 'height', 'count', 'transform')}
    meta['dtype'] = 'float32'
    meta['count'] = 1
    meta['compress'] = 'lzw'

    for date in pd.date_range('2016-01-01', '2022-01-01'):
        files = get_sat_path(date.strftime('%Y%m%d'))
        mean_array = get_daily_mean(files)
        if not mean_array.size:
            continue
        print(date)
        write_raster(
            out_path.format(date.strftime('%Y%m%d')),
            # np.round(np.power(10, mean_array), 4),
            mean_array,
            meta
        )
