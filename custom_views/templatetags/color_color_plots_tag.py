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
def color_color_diagram(target):

    def fetch_color_data_for_field(field_target,plot_limits):

        params = {}

        qs_col_x = ReducedDatum.objects.filter(source_name=field_target.name+'_pri_ref_gr')
        qs_col_y = ReducedDatum.objects.filter(source_name=field_target.name+'_pri_ref_ri')

        col_x_data = json.loads(qs_col_x[0].value)
        col_y_data = json.loads(qs_col_y[0].value)

        col_x = np.array(col_x_data['magnitude'])
        col_y = np.array(col_y_data['magnitude'])

        idx1 = np.where(col_x >= plot_limits['gr_min'])[0]
        idx2 = np.where(col_x <= plot_limits['gr_max'])[0]
        idx3 = np.where(col_y >= plot_limits['ri_min'])[0]
        idx4 = np.where(col_y <= plot_limits['ri_max'])[0]

        idx = set(idx1).intersection(set(idx2))
        idx = idx.intersection(set(idx3))
        idx = list(idx.intersection(set(idx4)))

        data = [ Column(name='gr', data=col_x[idx]),
                 Column(name='ri', data=col_y[idx]) ]

        colour_data = Table(data=data)

        return colour_data

    plot_limits = {'ri_min': 0.0, 'ri_max': 1.5,
                    'gr_min': 0.5, 'gr_max': 3.0}
    colour_data = fetch_color_data_for_field(target, plot_limits)

    if len(colour_data) > 0:

        fig = go.Figure()

        fig.add_trace(
                    go.Scatter(
                        x=colour_data['gr'],
                        y=colour_data['ri'],
                        mode="markers",
                        marker=dict(size=0.5,
                                    color='#03cbb1',
                                    line=dict(width=2,
                                        color='#03cbb1')),
                    )
                )

        fig.update_xaxes(
                    visible=True,
                    range=[plot_limits['gr_min'], plot_limits['gr_max']],
                    title=go.layout.xaxis.Title(
                        text='SDSS (g-r) [mag]',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white'
                )

        fig.update_yaxes(
                    visible=True,
                    range=[plot_limits['ri_min'], plot_limits['ri_max']],
                    #scaleanchor="x",
                    title=go.layout.yaxis.Title(
                        text='SDSS (r-i) [mag]',
                        font=dict(
                            size=18,
                            color='white')),
                    linecolor='white',
                    color = 'white',
                )

        fig.update_layout(
                    title='Colour-colour Diagram',
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
