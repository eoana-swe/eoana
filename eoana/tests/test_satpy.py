#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-12-07 11:09

@author: johannes
"""
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from satpy import Scene, find_files_and_readers


if __name__ == '__main__':
    sen3_data_l2 = 'C:/Temp/Satellit/sentinel_data'

    # datetime(YEAR, MOMNTH, DAY, HOUR, MINUTE)
    filenames = find_files_and_readers(
        start_time=datetime(2021, 7, 25, 7, 20),
        end_time=datetime(2021, 7, 25, 11, 25),
        base_dir=sen3_data_l2,
        reader='olci_l2',
        sensor='olci',
    )

    """ Create Scene object """
    scn = Scene(filenames=filenames)

    """ Load selected datasets 
        Available OLCI Level 2 datasets are:
            'chl_nn.nc','chl_oc4me.nc',
            'iop_nn.nc','iwv.nc','par.nc','trsp.nc','tsm_nn.nc','w_aer.nc',
            'Oa01_reflectance.nc','Oa02_reflectance.nc','Oa03_reflectance.nc','Oa04_reflectance.nc','Oa05_reflectance.nc','Oa06_reflectance.nc','Oa07_reflectance.nc','Oa08_reflectance.nc','Oa09_reflectance.nc','Oa10_reflectance.nc','Oa11_reflectance.nc','Oa12_reflectance.nc','Oa16_reflectance.nc','Oa17_reflectance.nc','Oa18_reflectance.nc','Oa21_reflectance.nc',
            'wqsf.nc'
    """
    datasets = ['Oa08', 'Oa06', 'chl_nn', 'chl_oc4me', 'mask']
    scn.load(datasets)

    """ Chlorophyll data are stored as logarithmic values. Convert to real values: """
    scn['chl_nn'] = np.power(10, scn['chl_nn'])

    plt.imshow(scn['chl_nn'])

