#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-02-12 15:04

@author: johannes
"""
import numpy as np
import pandas as pd
from bokeh.layouts import row, column
from bokeh.models.annotations import Title
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    Select,
    Circle,
    DatetimeTickFormatter,
    LinearColorMapper,
    ColorBar,
    TapTool,
    HoverTool,
    WheelZoomTool,
    ResetTool,
    PanTool,
    SaveTool,
)
from bokeh.models.tickers import MonthsTicker
from bokeh.plotting import figure, show, output_file
from pyproj import CRS, transform

from eoana.handlers.bokeh_map import get_map
from sharkweb_data_handler import get_sharkdata

output_file("chl_nn_water_body_validation_2016-2021.html")


def convert_projection(lats, lons):
    """Convert coordinates to a different system."""
    project_projection = CRS('EPSG:4326')
    google_projection = CRS('EPSG:3857')
    x, y = transform(project_projection, google_projection, lons, lats,
                     always_xy=True)
    return x, y


def get_source(path, ts_column=None, lat_col=None, lon_col=None, data=None,
               set_x=False, set_y=False, return_df_too=False):
    """Doc."""
    df = pd.read_csv(
        path,
        sep='\t',
    )
    if ts_column:
        df[ts_column] = df[ts_column].apply(lambda x: pd.Timestamp(str(x)))
        df['datestring'] = df[ts_column].dt.strftime('%Y-%m-%d')
    if lat_col and lon_col:
        xs, ys = convert_projection(df[lat_col].astype(float).values,
                                    df[lon_col].astype(float).values)
        df[lon_col] = xs
        df[lat_col] = ys
    if set_x:
        df['x'] = 0
    if set_y:
        df['y'] = 0
    if type(data) == pd.DataFrame:
        set_pos_source_attributes(df, data)

    if return_df_too:
        return ColumnDataSource(df), df
    else:
        return ColumnDataSource(df)


def get_running_mean_source(df_data):
    """Doc."""
    df_roll = df_data.copy()
    for col in df_roll:
        if col.startswith('SE'):
            rolling = df_roll[col].rolling(30, min_periods=3, center=True)
            df_roll[col] = rolling.mean()
            if not df_roll[col].any():
                df_roll[col].iloc[0] = 0
                df_roll[col].iloc[-1] = 0
    return ColumnDataSource(df_roll)


def get_shark_source(wb_mapper=None):
    """Doc."""
    shark_df = get_sharkdata('sharkweb_data.txt')
    df = shark_df.pivot(index='SDATE', columns='SEA_AREA_CODE', values='VALUE').reset_index()
    df['date'] = [pd.Timestamp(i) for i in df['SDATE']]
    df['datestring'] = df['date'].dt.strftime('%Y-%m-%d')
    df['y'] = 0
    df = df.rename(columns=wb_mapper)
    for c in wb_mapper.values():
        if c not in df:
            df[c] = np.nan
    return ColumnDataSource(df)


def set_pos_source_attributes(p_source, df):
    """Doc."""
    mapper = {'count': 'count (number of values)', 'mean': 'mean (µg/l)',
              'median': 'median (µg/l)', 'std': 'std (µg/l)',
              'var': 'var (µg/l)'}
    seasons = {'annual': list(range(1, 13)), 'spring': (3, 4, 5),
               'summer': (6, 7, 8), 'autumn': (9, 10, 11)}
    chl_cols = [c for c in df.columns if c[:2] == 'SE']
    for attr, name in mapper.items():
        for season, months in seasons.items():
            col_name = '-'.join((name, season))
            boolean = df['date'].dt.month.isin(months)
            attr_values = df.loc[boolean, chl_cols].__getattribute__(attr)()
            p_source[col_name] = [attr_values.get(wb, np.nan)
                                  for wb in p_source['VISS_EU_CD']]


def update_colormapper(fig=None, plot=None, color_mapper=None, color_bar=None,
                       data_source=None, x_sel=None, map_para_sel=None,
                       map_season_sel=None):
    """Update the color map."""
    code = """
        var parameter = map_para_sel.value;
        var season = map_season_sel.value;
        var column = parameter + '-' + season;
        console.log('column', column)
        const {transform} = renderer.glyph.fill_color;
        transform.low = color_mapper[column].low;
        transform.high = color_mapper[column].high;

        renderer.glyph.fill_color = {field: column, transform: transform};
        fig.reset.emit();
    """
    return CustomJS(
        args=dict(fig=fig, renderer=plot, color_mapper=color_mapper,
                  data_source=data_source, x_sel=x_sel, color_bar=color_bar,
                  map_para_sel=map_para_sel, map_season_sel=map_season_sel),
        code=code)


def wb_selection_callback(position_source=None, data_source=None,
                          shark_source=None, running_source=None, figure=None,
                          title_obj=None):
    """Return a CustomJS callback."""
    # assert position_source, data_source
    code = """
    // Get data from ColumnDataSource
    var position_data = position_source.data;

    // Get indices array of all selected items
    var idx = position_source.selected.indices;

    // Update active keys in data source
    if (idx.length == 1) {
        var selected_wb = position_data['VISS_EU_CD'][idx];
        data_source.data['y'] = data_source.data[selected_wb];
        running_source.data['y'] = running_source.data[selected_wb];
        shark_source.data['y'] = shark_source.data[selected_wb];
        
        title_obj.text = position_data['NAMN'][idx];

        // Save changes to ColumnDataSource
        data_source.change.emit();
        running_source.change.emit();
        shark_source.change.emit();
    } else {
        console.log('We can only work with one woter body at a time', 
        selected.length)
    }
    figure.reset.emit()
    """
    # Create a CustomJS callback with the code and the data
    return CustomJS(args={'position_source': position_source,
                          'data_source': data_source,
                          'shark_source': shark_source,
                          'running_source': running_source,
                          'title_obj': title_obj,
                          'figure': figure,
                          },
                    code=code)


data_source, df = get_source('waterbody_chl_nn_2016-2021_ver003.txt', ts_column='date',
                             set_x=True, set_y=True, return_df_too=True)

position_source, pos_df = get_source('waterbodies_info.txt', lat_col='latit',
                                     lon_col='longi', data=df,
                                     return_df_too=True)

running_source = get_running_mean_source(df)

shark_source = get_shark_source(
    wb_mapper={cw: vid for cw, vid in zip(pos_df['CWVattenID'], pos_df['VISS_EU_CD'])}
)

pan = PanTool()
save = SaveTool()
tap = TapTool()
reset = ResetTool()
wheel = WheelZoomTool()
tooltips = HoverTool(tooltips=[("Name", "@NAMN"),
                               ("Vatten ID", "@VattenID"),
                               ("CW Vatten ID", "@CWVattenID"),
                               ("VISS_EU_CD", "@VISS_EU_CD"),
                               ("VISS_MS_CD", "@VISS_MS_CD")])
fig_map = get_map()
fig_map.tools = [pan, wheel, tap, tooltips, reset, save]
fig_map.toolbar.active_scroll = wheel

color_mapper = {}
parameters = ['count (number of values)', 'mean (µg/l)',
             'median (µg/l)', 'std (µg/l)', 'var (µg/l)']
for para in parameters:
    for season in ['annual', 'spring', 'summer', 'autumn']:
        name = '-'.join((para, season))
        color_mapper[name] = LinearColorMapper(
            palette='Turbo256',
            low=pos_df[name].quantile(.01, interpolation='higher'),
            high=pos_df[name].quantile(.99, interpolation='lower')
        )

# dummy_cm: not ideal, but it works..
dummy_cm = LinearColorMapper(
    palette='Turbo256',
    low=0, high=200
)

map_renderer = fig_map.circle(
    x="longi",
    y="latit",
    fill_color={'field': 'count (number of values)-annual',
                'transform': dummy_cm},
    line_color=None,
    size=10, alpha=0.5, source=position_source,
)
nonselected_circle = Circle(fill_alpha=0.3, line_color='grey')
map_renderer.nonselection_glyph = nonselected_circle

color_bar = ColorBar(
    color_mapper=dummy_cm,
    label_standoff=14,
    location=(0, 0),
    # title='Number of annual values',
    # title_text_align="right",
)

fig_map.add_layout(color_bar, 'right')

map_para_sel = Select(value='count (nr)', options=parameters, max_width=200,
                      title='Select map point attribute')
map_season_sel = Select(value='annual', options=['annual', 'spring', 'summer', 'autumn'], max_width=200,
                        title='Select season')

cm_map_callback = update_colormapper(fig=fig_map, plot=map_renderer,
                                     color_mapper=color_mapper,
                                     color_bar=color_bar,
                                     map_para_sel=map_para_sel,
                                     map_season_sel=map_season_sel,
                                     data_source=data_source)

map_para_sel.js_on_change("value", cm_map_callback)
map_season_sel.js_on_change("value", cm_map_callback)

TOOLTIPS = [
    ("Date", "@datestring"),
    ("Chlorophyll a", "@y (µg/l)")
]
ts = figure(
    width=800, height=350, x_axis_type='datetime',
    y_axis_label='Chlorophyll (µg/l)',
    tooltips=TOOLTIPS
)
title_label = Title()
title_label.text = 'Waterbody chlorophyll a (chl_nn - Sentinel 3 and SHARK)'
ts.title = title_label
ts.circle(
    'date', 'y', size=7,
    color="#03B43F",
    alpha=.7,
    legend_label='Satellite gmean',
    source=data_source,
)
ts.line('date', 'y', color="#03B43F", source=running_source)
ts.circle(
    'date', 'y', size=7,
    color="#F9A52D",
    alpha=.7,
    legend_label='SHARK mean',
    source=shark_source,
)


# ts.xaxis.ticker = MonthsTicker(months=list(range(1, 13)))
# ts.xaxis.formatter = DatetimeTickFormatter(months="%b\n%Y")

fig_cb = wb_selection_callback(position_source=position_source,
                               data_source=data_source,
                               running_source=running_source,
                               shark_source=shark_source,
                               figure=ts,
                               title_obj=title_label)
tap.callback = fig_cb

show(
    row(column(fig_map), column(ts, map_para_sel, map_season_sel)),
)
