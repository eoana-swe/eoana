#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-13 17:57

@author: johannes
"""
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from pyproj import CRS, transform


class HelcomBasin:
    """Doc."""

    def __init__(self, shp_path=None):
        self.shapes = gp.read_file(shp_path)

    def find_area_for_point(self, lat, lon):
        """Return area information about the given location.

        Includes polygon.
        """
        boolean = self.shapes.contains(Point(float(lon), float(lat)))
        if any(boolean):
            return self.shapes.loc[boolean, 'level_3'].values[0]
            # return self.shapes.loc[boolean, 'HELCOM_ID'].values[0]
        else:
            return ''

    def get_polylines(self, boolean_basins):
        """Doc."""
        line_list = []
        for line_ring in self.shapes.loc[boolean_basins, 'geometry'].exterior:
            x_coords, y_coords = convert_projection(*line_ring.xy)
            line_list.append(([int(x) for x in x_coords],
                              [int(y) for y in y_coords]))
        return line_list


def convert_projection(lons, lats):
    """Convert coordinates to a different system."""
    project_projection = CRS('EPSG:4326')
    google_projection = CRS('EPSG:3857')
    x, y = transform(project_projection, google_projection, lons, lats,
                     always_xy=True)
    return x, y


def get_sharkdata(path):
    df = pd.read_csv(
        path,
        sep='\t',
        header=0,
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )
    df = df.loc[df['VALUE'].ne(''), ['SDATE', 'SEA_AREA_CODE', 'VALUE']]
    df['VALUE'] = df['VALUE'].astype(float)

    grouped_df = df.groupby(
        ['SDATE', 'SEA_AREA_CODE']
    ).mean().reset_index()
    grouped_df['SDATE'] = grouped_df['SDATE'].apply(pd.Timestamp)
    return grouped_df


def set_basin_info(path, shapes=None):
    df = pd.read_csv(
        path,
        sep='\t',
        header=0,
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )
    df['HELCOM_BASIN'] = ''
    df['pos_combo'] = df[['LATIT_DD', 'LONGI_DD']].apply('-'.join, axis=1)
    unique_pos = df['pos_combo'].unique()

    for pos_str in unique_pos:
        area_tag = shapes.find_area_for_point(*pos_str.split('-'))
        boolean = df['pos_combo'] == pos_str
        df.loc[boolean, 'HELCOM_BASIN'] = area_tag

    cols = ['MYEAR', 'STATN', 'REP_STATN_NAME', 'SHIPC', 'VISITID',
            'SDATE', 'STIME', 'LATIT_DD', 'LONGI_DD',
            'VALUE', 'HELCOM_BASIN']
    boolean = df['HELCOM_BASIN'].ne('')
    return df.loc[boolean, cols].reset_index(drop=True)


def get_basin_sharkdata(path):
    df = pd.read_csv(
        path,
        sep='\t',
        header=0,
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )
    df = df.loc[df['VALUE'].ne(''), ['SDATE', 'HELCOM_BASIN', 'VALUE']]
    df['VALUE'] = df['VALUE'].astype(float)

    grouped_df = df.groupby(
        ['SDATE', 'HELCOM_BASIN']
    ).mean().reset_index()
    grouped_df['SDATE'] = grouped_df['SDATE'].apply(pd.Timestamp)
    return grouped_df


def grouped_and_mean_sharkdata(path):
    cols = ['MYEAR', 'STATN', 'REP_STATN_NAME', 'SHIPC', 'VISITID',
            'SDATE', 'STIME', 'LATIT_DD', 'LONGI_DD',
            'DEPH', 'VALUE', 'QFLAG']
    df = pd.read_csv(
        path,
        sep='\t',
        header=0,
        encoding='cp1252',
        dtype=str,
        keep_default_na=False,
    )
    df = df.loc[df['VALUE'].ne('') & ~df['QFLAG'].isin(['B', 'S']), cols]
    df['VALUE'] = df['VALUE'].astype(float)

    grouped_df = df.groupby(cols[:-3]).mean().reset_index()
    grouped_df['VALUE'] = grouped_df['VALUE'].round(3)

    return grouped_df


if __name__ == '__main__':
    # shark_vis_mean = grouped_and_mean_sharkdata(
    #     r'C:\Temp\nis_satellit\sharkweb_data.txt'
    # )
    #
    # shark_vis_mean.to_csv(
    #     r'C:\Temp\nis_satellit\sharkweb_data_visit_mean.txt',
    #     sep='\t',
    #     index=False,
    #     encoding='cp1252'
    # )

    # shark_df = get_sharkdata(r'C:\Temp\nis_satellit\sharkweb_data.txt')
    # df = shark_df.pivot(index='SDATE', columns='SEA_AREA_CODE', values='VALUE').reset_index()
    # df['date'] = [pd.Timestamp(i) for i in df['SDATE']]
    # df['datestring'] = df['date'].dt.strftime('%Y-%m-%d')
    #
    shp_handler = HelcomBasin(
        shp_path=r'C:\Temp\shapes\sweden_helcom_shapes\helcom_ospar.shp')
    # # boolean = shp_handler.shapes['HELCOM_ID'].str.startswith('SEA')
    # # plines = shp_handler.get_polylines(boolean)
    df = set_basin_info(
        # 'sharkweb_data_all_chl_2020_incl_helcom_basins.txt',
        r'C:\Temp\nis_satellit\sharkweb_data_visit_mean.txt',
        shapes=shp_handler
    )

    # df = get_basin_sharkdata('sharkweb_data_all_chl_2016-2021_incl_helcom_basins.txt')

    df.to_csv(
        'sharkweb_data_all_chl_2016-2021_incl_helcom_basins.txt',
        sep='\t',
        index=False,
        encoding='cp1252'
    )
