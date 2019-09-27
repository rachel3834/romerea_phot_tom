import json

from django import template
from django.core.paginator import Paginator
from datetime import datetime

from plotly import offline
import plotly.graph_objs as go
from astropy.coordinates import SkyCoord
from astropy.table import Table, Column
import numpy as np
from os import path, getcwd
import json
from tom_targets.models import Target, TargetExtra
from tom_dataproducts.models import ReducedDatum

register = template.Library()

class Lightcurve():

    def __init__(self):
        self.dataset_code = None
        self.hjd  = []
        self.mag = []
        self.mag_err = []

@register.inclusion_tag('custom_views/plot_display.html')
def plot_lightcurve(target):

    def fetch_lc_data_for_star(target,plot_limits):

        params = {}

        star_id = str(target.name).split('-')[-1]

        qs = ReducedDatum.objects.filter(source_name__contains=star_id)

        datasets = {}
        for entry in qs:
            data = json.loads(entry.value)
            if data['filter'] in datasets.keys():
                lc_data = datasets[data['filter']]
            else:
                lc_data = Lightcurve()

            if 'fa15' in entry.source_name or 'fl15' in entry.source_name:
                lc_data.dataset_code = data['filter']
                if float(data['magnitude']) > 0.0 and \
                    float(data['magnitude_error']) > 0.0 and float(data['magnitude_error']) <= 0.05:
                    lc_data.hjd.append(float(data['hjd']) - 2450000.0)
                    lc_data.mag.append(float(data['magnitude']))
                    lc_data.mag_err.append(float(data['magnitude_error']))

                datasets[data['filter']] = lc_data

        for code, lc_data in datasets.items():
            table_data = [ Column(name='hjd', data=lc_data.hjd),
                            Column(name='mag', data=lc_data.mag),
                            Column(name='mag_err', data=lc_data.mag_err) ]
            datasets[code] = Table(data=table_data)

        return datasets

    plot_limits = {'bright_g': 14.0, 'faint_g': 22.0,
                    'gi_min': 0.5, 'gi_max': 4.5}
    plot_colours = { 'gp': '#0AD503',
                     'rp': '#F4ED0B',
                     'ip': '#D51D03'}
    datasets = fetch_lc_data_for_star(target, plot_limits)

    if len(datasets) > 0:

        fig = go.Figure()

        for code, lc_data in datasets.items():

            trace_colour = plot_colours[code]

            fig.add_trace(
                        go.Scatter(
                            x=np.array(lc_data['hjd']),
                            y=np.array(lc_data['mag']),
                            error_y=dict(type='data',
                                        array=np.array(lc_data['mag_err']),
                                        visible=True),
                            name=code,
                            mode="markers",
                            marker=dict(size=0.5,
                                        color=trace_colour,
                                        line=dict(width=2,
                                            color=trace_colour)),
                        )
                    )

        fig.update_xaxes(
                    visible=True,
                    #range=[plot_limits['gi_min'], plot_limits['gi_max']],
                    title=go.layout.xaxis.Title(
                        text='HJD - 2450000.0',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white'
                )

        fig.update_yaxes(
                    visible=True,
                    #range=[plot_limits['bright_g'], plot_limits['faint_g']],
                    title=go.layout.yaxis.Title(
                        text='Magnitude',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white',
                    autorange='reversed',
                )

        fig.update_layout(
                    title='Lightcurves of star '+target.name,
                    font=dict(color="white",size=20),
                    width=700,
                    height=700,
                    margin={"l": 55, "r": 15, "t": 55, "b": 55},
                    plot_bgcolor='black',
                    paper_bgcolor='black',
                )

        return {
            'target': target,
            'plot': offline.plot(fig, output_type='div', show_link=False)
        }

    else:

        plot = '<div></div>'

        return {'target': target,
                'plot': plot}
