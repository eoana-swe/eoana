#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-12-07 11:33

@author: johannes
"""
import os
import numpy as np
import pandas as pd
import geopandas as gp
import matplotlib.pyplot as plt
from datetime import datetime
from satpy import Scene, find_files_and_readers
from pyresample import load_area
from eoana.config import Settings
from eoana import utils


if __name__ == '__main__':
    settings = Settings()
    basin_grid = settings.get_basin_grid()
    bbox = settings.get_basin_grid_corners()
    bottom, left = utils.transform_ref_system(lat=bbox.bottom, lon=bbox.left)
    top, right = utils.transform_ref_system(lat=bbox.top, lon=bbox.right)
    grid_poly = utils.get_polygon(llc=(left, bottom), urc=(right, top))

    my_area = load_area(
        os.path.join(settings.base_directory, 'etc/areas/local_areas.yaml'),
        'baws300_hanobay_sweref99tm'
    )

    # months = set('5')
    months = set([str(n) for n in range(5, 10)])
    directory = r'..\proj\sentineldata\2020\OLCI'
    data_folders = {
        f[16:31]: os.path.join(directory, f) for f in os.listdir(directory) if f[21] in months
    }
    parameters = ('chl_nn.nc', 'wqsf.nc', 'tie_geometries.nc', 'geo_coordinates.nc')
    datasets = ['chl_nn', 'wqsf']

    means = {key: [] for key in ('timestamp', 'mean_chl_nn')}
    for ts, data_folder in data_folders.items():
        filenames = {'olci_l2': [os.path.join(data_folder, f) for f in parameters]}

        """ Create Scene object """
        scn = Scene(filenames=filenames)
        scn.load(datasets)
        scn_poly = utils.get_polygon(coord_list=scn['chl_nn'].area.corners)

        if grid_poly.intersects(scn_poly):
            print('Using:', data_folder)
            scn = scn.resample(my_area, radius_of_influence=800)

            mask = utils.get_mask(scn)
            sea_area_data = scn['chl_nn'].where(
                np.logical_and(basin_grid == 45, ~mask),
                np.nan
            )

            mean_value = np.nanmean(sea_area_data)
            if not np.isnan(mean_value):
                means['timestamp'].append(ts)
                means['mean_chl_nn'].append(mean_value)
        # else:
        #     print('NOT:', data_folder)
            # print(scn_poly.exterior.coords.xy)
            # if '20200501T092901_20200501T093201' in data_folder:
            #     break

    df = pd.DataFrame(means)
    df['mean_chl_nn'] = df['mean_chl_nn'].apply(lambda x: np.power(10, x))
    df.to_csv('mean_chl_nn_2020.txt',
              sep='\t',
              index=False)
