#!/usr/bin/env python3
"""
Created on 2022-10-16 11:41

@author: johannes
"""
import os
from pathlib import Path
from datetime import datetime
from eoana.handlers.file_searcher import Seacher
import warnings
warnings.filterwarnings('ignore')


if __name__ == '__main__':
    # sen3_data_l2 = r'E:\sentinel_3_data\olci_level_2'
    sen3_data_l2 = r'D:\olci_l2_003'
    folder = r'C:\Temp\Satellit\olci_output\helcom'
    ticker = 0
    for fname in Path(r'C:\Temp\Satellit\olci_output\helcom').glob('*.tiff'):
        ct = datetime.fromtimestamp(Path(fname).stat().st_ctime)
        mt = datetime.fromtimestamp(Path(fname).stat().st_mtime)
        if mt.month != 10:
            print(fname, ct, mt)
            ticker += 1
            # fname.unlink()
    # searcher = Seacher(base_dir=sen3_data_l2, satpy_reader='olci_l2')
    # files_ready = os.listdir(r'C:\Temp\Satellit\olci_output\helcom')
    # for date in searcher.passages.keys():
    #     for passage in searcher.passages[date].keys():
    #         # if passage.startswith('S3A'):
    #         #     continue
    #
    #         name = '_'.join(
    #             (passage, scn.start_time.strftime('%Y%m%d_%H%M'), 'chl_nn'))
    #         filename=fr'C:\Temp\Satellit\olci_output\helcom\{name}.tiff',
