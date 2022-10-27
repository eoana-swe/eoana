#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-11 08:22

@author: johannes
"""
import os
import rasterio as rio
from satpy import Scene
from eoana.handlers.file_searcher import Seacher
from eoana.config import Settings
import numpy as np
from pyresample import load_area
import time
from functools import reduce
import warnings
warnings.filterwarnings('ignore')


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


def get_zone_mask(path):
    rst = rio.open(path)
    array = rst.read()
    return array[0]


FLAGS002 = [
    "INVALID", "SNOW_ICE", "INLAND_WATER", "SUSPECT", "AC_FAIL",
    "CLOUD", "HISOLZEN", "CLOUD_MARGIN", "CLOUD_AMBIGUOUS", "LOWRW", "LAND"
]
FLAGS003 = [
    "INVALID", "SNOW_ICE", "INLAND_WATER", "SUSPECT", "AC_FAIL", "CLOUD",
    "HISOLZEN", "CLOUD_MARGIN", "CLOUD_AMBIGUOUS", "COASTLINE", "LAND",
    "TURBID_ATM", "LOWRW"
]


def get_flag_mask(scene):
    bflags = BitFlags(scene['wqsf'].attrs['flag_masks'],
                      scene['wqsf'].attrs['flag_meanings'].split())

    return bflags.match_any(FLAGS003, scene['wqsf'])
    # try:
    #     return bflags.match_any(FLAGS003, scn['wqsf'])
    # except:
    #     return bflags.match_any(FLAGS002, scn['wqsf'])


if __name__ == '__main__':
    settings = Settings()

    coastal_mask = get_zone_mask(
        os.path.join(settings.base_directory,
                     'etc/basin_grid/helcom_ospar.tiff',
                     # 'etc/basin_grid/HELCOM_subbasins_2018_incl_skagerrak.tiff',
                     # 'etc/basin_grid/SVAR_2016_3b_coastal_zone.tiff'
                     )
    )

    area_spec = load_area(
        os.path.join(settings.base_directory, 'etc/areas/areas_baws.yaml'),
        'baws300_sweref99tm'
    )

    # sen3_data_l2 = '/data/proj/sentineldata/2020/OLCI'
    # sen3_data_l2 = r'E:\sentinel_3_data\olci_level_2'
    sen3_data_l2 = r'D:\olci_l2_003'
    searcher = Seacher(base_dir=sen3_data_l2, satpy_reader='olci_l2')
    # files_ready = os.listdir(r'C:\Temp\Satellit\olci_output\helcom')
    # raise EOFError

    for date in searcher.passages.keys():
        # if date.startswith('2021'):
        #     if int(date[4:6]) > 4:
        #         continue
        #     elif (int(date[4:6]) == 4) and (int(date[6:8]) > 28):
        #         continue
        for passage in searcher.passages[date].keys():
            # if passage.startswith('S3A'):
            #     continue
            filenames = searcher.get_passage_files(date, passage)
            size = 0
            for fid in filenames['olci_l2']:
                _size = os.stat(fid).st_size / (1024**2)
                if _size > size:
                    size = _size
            if size > 100:  # Sometimes files are strangely large..
                continue
            print(date, passage)
            start_time = time.time()
            date_passage_passed = False
            while not date_passage_passed:
                scn = Scene(filenames=filenames)
                scn.load(['chl_nn', 'wqsf'])

                scn = scn.resample(area_spec, radius_of_influence=500)
                mask = get_flag_mask(scn)
                scn['chl_nn'] = scn['chl_nn'].where(coastal_mask > 0, np.nan)
                scn['chl_nn'] = scn['chl_nn'].where(mask != True, np.nan)
                name = '_'.join(
                    (passage, scn.start_time.strftime('%Y%m%d_%H%M'), 'chl_nn'))
                scn.save_dataset(
                    'chl_nn',
                    filename=fr'C:\Temp\Satellit\olci_output\helcom\{name}.tiff',
                    dtype=np.float32,
                    enhance=False
                )
                print("Timeit:--%.1f sec" % (time.time() - start_time))
                date_passage_passed = True

    # passes = []
    # for d, item in searcher.passages.items():
    #     passes.extend(item.keys())
