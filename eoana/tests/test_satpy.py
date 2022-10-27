#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-12-07 11:09

@author: johannes
"""
import os
import numpy as np
import geopandas as gp
import matplotlib.pyplot as plt
from datetime import datetime
from satpy import Scene, find_files_and_readers
from pyresample import load_area

from eoana.config import Settings
from eoana import utils
"""
from datetime import datetime
from satpy import Scene, find_files_and_readers
directory = '/data/proj/sentineldata/2020/OLCI'
filenames = find_files_and_readers(
    start_time=datetime(2020, 7, 25, 7, 20),
    end_time=datetime(2020, 7, 25, 11, 25),
    base_dir=directory,
    reader='olci_l2',
    sensor='olci',
)
scn = Scene(filenames=filenames)
datasets = ['Oa08', 'Oa06', 'chl_nn', 'chl_oc4me', 'mask']
scn.load(datasets)
"""

if __name__ == '__main__':
    settings = Settings()
    bbox = settings.get_basin_grid_corners()
    bottom, left = utils.transform_ref_system(lat=bbox.bottom, lon=bbox.left)
    top, right = utils.transform_ref_system(lat=bbox.top, lon=bbox.right)
    grid_poly = utils.get_polygon(llc=(left, bottom), urc=(right, top))

    # directory = 'C:/Temp/Satellit/sentinel_data'

    # datetime(YEAR, MOMNTH, DAY, HOUR, MINUTE)
    # filenames = find_files_and_readers(
    #     start_time=datetime(2021, 7, 25, 7, 20),
    #     end_time=datetime(2021, 7, 25, 11, 25),
    #     base_dir=directory,
    #     reader='olci_l2',
    #     sensor='olci',
    # )
    directory = r'..proj\sentineldata\2020\OLCI\S3A_OL_2_WFR____20200720T081412_20200720T081712_20200721T170052_0179_060_349_1980_MAR_O_NT_002.SEN3'
    filenames = {
        'olci_l2': [
            os.path.join(directory, f) for f in ('chl_nn.nc', 'wqsf.nc', 'tie_geometries.nc',
                                                 'geo_coordinates.nc')
        ]
    }

    """ Create Scene object """
    scn = Scene(filenames=filenames)

    """ Load selected datasets
        Available OLCI Level 2 datasets are:
            'chl_nn.nc','chl_oc4me.nc',
            'iop_nn.nc','iwv.nc','par.nc','trsp.nc','tsm_nn.nc','w_aer.nc',
            'Oa01_reflectance.nc','Oa02_reflectance.nc','Oa03_reflectance.nc','Oa04_reflectance.nc',
            'Oa05_reflectance.nc','Oa06_reflectance.nc','Oa07_reflectance.nc','Oa08_reflectance.nc',
            'Oa09_reflectance.nc','Oa10_reflectance.nc','Oa11_reflectance.nc','Oa12_reflectance.nc',
            'Oa16_reflectance.nc','Oa17_reflectance.nc','Oa18_reflectance.nc','Oa21_reflectance.nc',
            'wqsf.nc'
    """
    datasets = [
        # 'Oa08', 'Oa06',
        'chl_nn',
        # 'chl_oc4me', 'mask'
    ]
    scn.load(datasets)
    scn_poly = utils.get_polygon(coord_list=scn['chl_nn'].area.corners)
    print('done')
    # print('load done.')
    # my_area = load_area(
    #     os.path.join(settings.base_directory, 'etc/areas/local_areas.yaml'), 'baws300_hanobay_sweref99tm'
    # )
    # scn = scn.resample(my_area, radius_of_influence=800)
    #
    # # """ Chlorophyll data are stored as logarithmic values. Convert to real values: """
    # # scn['chl_nn'] = np.power(10, scn['chl_nn'])
    # scn.save_dataset(
    #     'chl_nn',
    #     filename='baws300_hanobay_sweref99tm_template.tiff',
    #     writer='geotiff',
    #     dtype=np.uint8,
    #     enhance=False,
    # )
    # plt.imshow(scn['chl_nn'])
    # plt.colorbar()
    # plt.clim(0, 10)
