import json

from django import template
from django.core.paginator import Paginator
from datetime import datetime

from plotly import offline
import plotly.graph_objs as go
from astropy.coordinates import SkyCoord
import numpy as np
from os import path, getcwd

from tom_targets.models import Target, TargetExtra

register = template.Library()
@register.inclusion_tag('custom_views/plot_display.html')
def color_mag_diagram(target):

    def fetch_color_data_for_field(field_target):

        params = {}

        keylist = ['cal_mag_corr_g', 'gi']

        qs_mag = TargetExtra.objects.filter(target__name__contains=field_target.name+'-', key='cal_mag_corr_g')
        qs_col = TargetExtra.objects.filter(target__name__contains=field_target.name+'-', key='gi')

        colour_data = []

        for j in stars:
            data = []

            for key in keylist:
                #qs = TargetExtra.objects.filter(target=j, key=key)

                gmag = j.cal_mag_corr_g
                gi = j.gi

                data = [ gmag, gi ]

                #if len(qs) > 0:
                #    data.append(float(qs[0].value))

            if len(data) == len(keylist):
                colour_data.append(data)
                print(data)

        return colour_data

    print('Got here for field '+repr(target))

    colour_data = fetch_color_data_for_field(target)

    if len(colour_data) > 0:

        fig = go.Figure()

        fig.add_trace(
                    go.Scatter(
                        x=colour_data[:,1],
                        y=colour_data[:,0],
                        mode="markers"
                    )
                )

        fig.update_xaxes(
                    visible=True,
                    range=[colour_data[:,1].max(),colour_data[:,1].min()],
                    title_text='SDSS (g-i) [mag]',
                    linecolor='white',
                    color = 'white'
                )

        fig.update_yaxes(
                    visible=True,
                    range=[colour_data[:,0].max(),colour_data[:,0].min()],
                    # the scaleanchor attribute ensures that the aspect ratio stays constant
                    scaleanchor="x",
                    title_text='SDSS-g [mag]',
                    linecolor='white',
                    color = 'white'
                )

        fig.update_layout(
                    width=(params['naxis1']*scale_factor),
                    height=(params['naxis2']*scale_factor),
                    margin={"l": 0, "r": 0, "t": 0, "b": 0},
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
