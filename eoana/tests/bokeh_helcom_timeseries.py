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

from eoana.handlers.bokeh_map import get_map
from sharkweb_data_handler import get_basin_sharkdata, HelcomBasin, convert_projection

output_file("chl_nn_helcom_basin_validation_2016-2021.html")


def get_basin_lines():
    """Doc."""
    shp_handler = HelcomBasin(shp_path=r'C:\Temp\shapes\sweden_helcom_shapes\helcom_ospar.shp')
    boolean = shp_handler.shapes['HELCOM_ID'].str.startswith('SEA')
    return shp_handler.get_polylines(boolean)


def get_source(path, ts_column=None, lat_col=None, lon_col=None, data=None,
               set_x=False, set_y=False, return_df_too=False,
               only_basins=False):
    """Doc."""
    df = pd.read_csv(
        path,
        encoding='cp1252',
        sep='\t',
    )
    if only_basins:
        df = df.loc[df['HELCOM_ID'].str.startswith('SEA'), :].reset_index(drop=True)
    if ts_column:
        df[ts_column] = df[ts_column].apply(lambda x: pd.Timestamp(str(x)))
        df['datestring'] = df[ts_column].dt.strftime('%Y-%m-%d')
    if lat_col and lon_col:
        xs, ys = convert_projection(df[lon_col].astype(float).values,
                                    df[lat_col].astype(float).values)
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
        if col not in ('date', 'datestring', 'x', 'y'):
            rolling = df_roll[col].rolling(30, min_periods=3, center=True)
            df_roll[col] = rolling.mean()
            if not df_roll[col].any():
                df_roll[col].iloc[0] = 0
                df_roll[col].iloc[-1] = 0
    return ColumnDataSource(df_roll)


def get_shark_source(wb_mapper=None):
    """Doc."""
    shark_df = get_basin_sharkdata(
        'sharkweb_data_all_chl_2016-2021_incl_helcom_basins_chl_nn_ver003.txt'
    )
    df = shark_df.pivot(index='SDATE', columns='HELCOM_BASIN', values='VALUE').reset_index()
    df['date'] = [pd.Timestamp(i) for i in df['SDATE']]
    df['datestring'] = df['date'].dt.strftime('%Y-%m-%d')
    df['y'] = 0
    df = df.rename(columns=wb_mapper)
    for c in wb_mapper.values():
        if c not in df:
            df[c] = np.nan
    return ColumnDataSource(df)


def get_shark_stations_source():
    """Doc."""
    df = pd.read_csv(
        'sharkweb_data_all_chl_2016-2021_incl_helcom_basins_chl_nn_ver003.txt',
        encoding='cp1252',
        sep='\t',
    )
    xs, ys = convert_projection(df['LONGI_DD'].astype(float).values,
                                df['LATIT_DD'].astype(float).values)
    df['longi'] = xs
    df['latit'] = ys
    selected_cols = ['STATN', 'longi', 'latit', 'HELCOM_BASIN']
    return ColumnDataSource(df[selected_cols])


def set_pos_source_attributes(p_source, df):
    """Doc."""
    mapper = {'count': 'count (number of values)', 'mean': 'mean (µg/l)',
              'median': 'median (µg/l)', 'std': 'std (µg/l)',
              'var': 'var (µg/l)'}
    seasons = {'annual': list(range(1, 13)), 'spring': (3, 4, 5),
               'summer': (6, 7, 8), 'autumn': (9, 10, 11)}
    chl_cols = [c for c in df.columns if c not in ('date', 'datestring', 'x', 'y')]
    for attr, name in mapper.items():
        for season, months in seasons.items():
            col_name = '-'.join((name, season))
            boolean = df['date'].dt.month.isin(months)
            attr_values = df.loc[boolean, chl_cols].__getattribute__(attr)()
            p_source[col_name] = [attr_values[wb]
                                  for wb in p_source['level_3']]


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
                          statn_source=None, plot_statn_source=None,
                          title_obj=None):
    """Return a CustomJS callback."""
    code = """
    // Get data from ColumnDataSource
    var position_data = position_source.data;
    var statn_source_data = statn_source.data;

    // Get indices array of all selected items
    var idx = position_source.selected.indices;

    // Update active keys in data source
    if (idx.length == 1) {
        var selected_wb = position_data['level_3'][idx];
        data_source.data['y'] = data_source.data[selected_wb];
        running_source.data['y'] = running_source.data[selected_wb];
        shark_source.data['y'] = shark_source.data[selected_wb];
        title_obj.text = position_data['level_3'][idx];

        var statn_data = {longi: [], latit: [], STATN: []};
        var longi_val, latit_val, statn_val, hc_id;
        for (var i = 0; i < statn_source_data.latit.length; i++) {
            longi_val = statn_source_data.longi[i];
            latit_val = statn_source_data.latit[i];
            statn_val = statn_source_data.STATN[i];
            hc_id = statn_source_data.HELCOM_BASIN[i];

            if (hc_id == selected_wb) {
                statn_data.longi.push(longi_val);
                statn_data.latit.push(latit_val);
                statn_data.STATN.push(statn_val);
            }
        }

        // Save changes to ColumnDataSource
        data_source.change.emit();
        running_source.change.emit();
        shark_source.change.emit();
        plot_statn_source.data = statn_data;
        plot_statn_source.change.emit();

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
                          'statn_source': statn_source,
                          'plot_statn_source': plot_statn_source,
                          'title_obj': title_obj,
                          'figure': figure,
                          },
                    code=code)


data_source, df = get_source(
    # 'basins_chl_nn_2020.txt',
    'basins_chl_nn_2016-2021_b.txt',
    ts_column='date',
    set_x=True, set_y=True, return_df_too=True
)

position_source, pos_df = get_source('helcom_basin_info.txt', lat_col='latit',
                                     lon_col='longi', data=df,
                                     return_df_too=True, only_basins=True)

shark_stations_source = get_shark_stations_source()
plot_stations_source = ColumnDataSource({
    'STATN': ['hej'], 'longi': [0], 'latit': [0]
})

running_source = get_running_mean_source(df)

shark_source = get_shark_source(
    wb_mapper={cw: cw for cw in pos_df['level_3']}
)

poly_lines = get_basin_lines()

pan = PanTool()
save = SaveTool()
tap = TapTool()
reset = ResetTool()
wheel = WheelZoomTool()
tooltips = HoverTool(tooltips=[("Name", "@level_3"),
                               ("Helcom ID", "@HELCOM_ID")])
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
start_para = 'count (number of values)-annual'
dummy_cm = LinearColorMapper(
    palette='Turbo256',
    low=pos_df[start_para].quantile(.01, interpolation='higher'),
    high=pos_df[start_para].quantile(.99, interpolation='lower')
)

map_renderer = fig_map.circle(
    x="longi",
    y="latit",
    fill_color={'field': 'count (number of values)-annual',
                'transform': dummy_cm},
    line_color=None,
    size=20, alpha=0.5, source=position_source,
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

fig_map.circle(
    x="longi",
    y="latit",
    color="#0087FF",
    line_color=None,
    size=7, alpha=0.5, source=plot_stations_source,
)
for pl in poly_lines:
    fig_map.line(
        x=pl[0],
        y=pl[1],
        color="grey",
    )

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
title_label.text = 'Basin chlorophyll a (chl_nn - Sentinel 3 and SHARK)'
ts.title = title_label
ts.circle(
    'date', 'y', size=7,
    color="#1EC600",
    alpha=.7,
    legend_label='Satellite gmean',
    source=data_source,
)
ts.line('date', 'y', color="#1EC600", source=running_source)
ts.circle(
    'date', 'y', size=7,
    color="#7A3CC0",
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
                               statn_source=shark_stations_source,
                               plot_statn_source=plot_stations_source,
                               figure=ts,
                               title_obj=title_label)
tap.callback = fig_cb

show(
    row(column(fig_map), column(ts, map_para_sel, map_season_sel)),
)
