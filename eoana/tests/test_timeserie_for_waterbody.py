#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-12-07 11:33

@author: johannes
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from satpy import Scene, find_files_and_readers
from pyresample import load_area

from eoana.config import Settings


if __name__ == '__main__':

    settings = Settings()

    sen3_data_l2 = 'C:/Temp/Satellit/sentinel_data'

    filenames = find_files_and_readers(
        start_time=datetime(2021, 7, 25, 7, 20),
        end_time=datetime(2021, 7, 25, 11, 25),
        base_dir=sen3_data_l2,
        reader='olci_l2',
        sensor='olci',
    )

    """ Create Scene object """
    scn = Scene(filenames=filenames)

    datasets = ['chl_nn', 'mask']
    scn.load(datasets)

    my_area = load_area(
        os.path.join(settings.base_directory, 'etc/areas/local_areas.yaml'), 'baws300_sweref99tm'
    )
    scn = scn.resample(my_area, radius_of_influence=800)

    """ Chlorophyll data are stored as logarithmic values. Convert to real values: """
    scn['chl_nn'] = np.power(10, scn['chl_nn'])
    plt.imshow(scn['chl_nn'])

