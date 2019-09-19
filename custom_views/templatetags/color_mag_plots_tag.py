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
@register.inclusion_tag('custom_views/plot_display.html')
def color_mag_diagram(target):

    def fetch_color_data_for_field(field_target,plot_limits):

        params = {}

        qs_mag = ReducedDatum.objects.filter(source_name=field_target.name+'_pri_ref_cal_mag_corr_g')
        qs_col = ReducedDatum.objects.filter(source_name=field_target.name+'_pri_ref_gi')

        mag_data = json.loads(qs_mag[0].value)
        col_data = json.loads(qs_col[0].value)

        mags = np.array(mag_data['magnitude'])
        cols = np.array(col_data['magnitude'])

        idx1 = np.where(mags >= plot_limits['bright_g'])[0]
        idx2 = np.where(mags <= plot_limits['faint_g'])[0]
        idx3 = np.where(cols >= plot_limits['gi_min'])[0]
        idx4 = np.where(cols <= plot_limits['gi_max'])[0]

        idx = set(idx1).intersection(set(idx2))
        idx = idx.intersection(set(idx3))
        idx = list(idx.intersection(set(idx4)))

        data = [ Column(name='g', data=mags[idx]),
                 Column(name='gi', data=cols[idx]) ]

        colour_data = Table(data=data)

        return colour_data

    plot_limits = {'bright_g': 14.0, 'faint_g': 22.0,
                    'gi_min': 0.5, 'gi_max': 4.5}
    colour_data = fetch_color_data_for_field(target, plot_limits)

    if len(colour_data) > 0:

        fig = go.Figure()

        fig.add_trace(
                    go.Scatter(
                        x=colour_data['gi'],
                        y=colour_data['g'],
                        mode="markers",
                        marker=dict(size=0.5,
                                    color='#03cbb1',
                                    line=dict(width=2,
                                        color='#03cbb1')),
                    )
                )

        fig.update_xaxes(
                    visible=True,
                    range=[plot_limits['gi_min'], plot_limits['gi_max']],
                    title=go.layout.xaxis.Title(
                        text='SDSS (g-i) [mag]',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white'
                )

        fig.update_yaxes(
                    visible=True,
                    range=[plot_limits['bright_g'], plot_limits['faint_g']],
                    #scaleanchor="x",
                    title=go.layout.yaxis.Title(
                        text='SDSS-g [mag]',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white',
                    autorange='reversed',
                )

        fig.update_layout(
                    title='Colour-magnitude Diagram',
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
