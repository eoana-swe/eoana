#!/usr/bin/env python3
"""
Created on 2021-09-27 17:59

@author: johannes
"""
import time
import json
import numpy as np
import pandas as pd
from eoana.utils import get_idx


if __name__ == '__main__':
    lat_array = np.load(r'latitude_baws300.npy')
    lon_array = np.load(r'longitude_baws300.npy')
    print('load complete')
    # Testing.
    # start_time = time.time()
    # idx = get_idx(lat_array, lon_array, 59., 20.)
    # print("Timeit:--%.5f sec" % (time.time() - start_time))

    data = pd.read_csv(
        r'sharkweb_data_all_chl_2016-2021_incl_helcom_basins.txt',
        header=0,
        sep='\t',
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )

    positions = data[['LATIT_DD', 'LONGI_DD']].apply(
        lambda x: '-'.join(x),
        axis=1
    )
    unique_positions = positions.unique()

    position_index = {}
    for i, pos in enumerate(unique_positions):
        if str(i).endswith('00'):
            print(i)
        lat, lon = pos.split('-')
        idx = get_idx(lat_array, lon_array, float(lat), float(lon))
        position_index.setdefault(pos, idx)

    with open('position_index.json', "w") as outfile:
        json.dump(position_index, outfile, indent=4)
