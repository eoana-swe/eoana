#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-10 19:38

@author: johannes
"""
import os
import pandas as pd

OLCI_FILES = [
    'chl_nn.nc',
    # 'chl_oc4me.nc',
    'geo_coordinates.nc',
    # 'Oa01_reflectance.nc', 'Oa02_reflectance.nc',
    # 'Oa03_reflectance.nc', 'Oa04_reflectance.nc', 'Oa05_reflectance.nc',
    # 'Oa06_reflectance.nc', 'Oa07_reflectance.nc', 'Oa08_reflectance.nc',
    # 'Oa09_reflectance.nc', 'Oa10_reflectance.nc', 'Oa11_reflectance.nc',
    # 'Oa12_reflectance.nc', 'Oa16_reflectance.nc', 'Oa17_reflectance.nc',
    # 'Oa18_reflectance.nc', 'Oa21_reflectance.nc',
    'tie_geometries.nc',
    'wqsf.nc',
    # 'trsp.nc', 'tsm_nn.nc', 'iop_nn.nc',
    # 'tie_geo_coordinates.nc', 'tie_meteo.nc', 'w_aer.nc',
    # 'instrument_data.nc', 'iwv.nc', 'par.nc', 'time_coordinates.nc',
]


def get_file_list(base_folder, directory):
    """Doc."""
    # Special structure.. :(
    folder = os.path.join(base_folder, directory, directory)
    if os.path.exists(folder):
        return [os.path.join(folder, f) for f in OLCI_FILES]
    else:
        return [os.path.join(base_folder, directory, f) for f in OLCI_FILES]


class Seacher:
    """Doc."""

    def __init__(self, base_dir=None, satpy_reader='olci_l2'):
        self.base_dir = base_dir
        self.satpy_reader = satpy_reader
        self.df = pd.DataFrame({
            'directories': [d for d in os.listdir(self.base_dir)
                            if d.endswith('.SEN3')]
        })
        self._set_name_attributes()

        self.passages = {}
        self._set_daily_passages()

    def get_passage_files(self, date, passage):
        """Doc."""
        return {self.satpy_reader: self.passages[date].get(passage)}

    def _set_name_attributes(self):
        """Doc."""
        start_ts = []
        satellite = []
        orbit = []
        for d in self.df['directories']:
            list_of_attributes = d.split('_')
            satellite.append(list_of_attributes[0])
            start_ts.append(list_of_attributes[7].split('T')[0])
            orbit.append(list_of_attributes[12])
        self.df['satellite'] = satellite
        self.df['orbit'] = orbit
        self.df['start_ts'] = start_ts

    def _set_daily_passages(self):
        """Doc."""
        for date in self.df['start_ts'].unique():
            boolean = self.df['start_ts'] == date

            sat_orb_complete = set()
            for row in self.df[boolean].itertuples():
                combo = f'{row.satellite}_{row.orbit}'
                if combo in sat_orb_complete:
                    continue
                else:
                    sat_orb_complete.add(combo)

                boolean_select = boolean & (self.df['orbit'] == row.orbit) \
                                 & (self.df['satellite'] == row.satellite)
                self._append_passage(date, combo, boolean_select)

    def _append_passage(self, date, combo, boolean_select):
        """Doc."""
        self.passages.setdefault(date, {})
        for row in self.df[boolean_select].itertuples():
            file_list = get_file_list(self.base_dir, row.directories)
            self.passages[date].setdefault(combo, []).extend(file_list)


if __name__ == '__main__':
    sen3_data_l2 = r'D:\olci_l2_003'
    searcher = Seacher(base_dir=sen3_data_l2, satpy_reader='olci_l2')
    searcher.passages.keys()
    # searcher.passages[date].keys()
    for fid in searcher.passages['20211224']['S3B_335']:
        print(os.stat(fid).st_size)