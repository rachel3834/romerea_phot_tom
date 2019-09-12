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

@register.inclusion_tag('custom_views/image_display.html')
def navigable_image(target):

    def fetch_image_params(target):

        params = {}

        keylist = ['naxis1', 'naxis2', 'pixscale']

        for key in keylist:
            qs = TargetExtra.objects.filter(target=target, key='naxis1')

            if len(qs) > 0:
                params[key] = float(qs[0].value)

        if len(params) == len(keylist):
            return params
        else:
            return {}

    params = fetch_image_params(target)

    image_file = path.join('/static','img',str(target.name)+'_colour.png')

    if len(params) > 0:
        half_width_y = (params['naxis1']/2.0) * params['pixscale']
        half_width_x = (params['naxis2']/2.0) * params['pixscale']

        xdata = np.arange(float(target.ra)-half_width_x,float(target.ra)+half_width_x,0.25)
        ydata = np.arange(float(target.dec)-half_width_y,float(target.dec)+half_width_y,0.25)

        scale_factor = 0.2

        fig = go.Figure()

        fig.add_trace(
                    go.Scatter(
                        #x=[0, (params['naxis2']*scale_factor)],
                        #y=[0, (params['naxis1']*scale_factor)],
                        x=xdata,
                        y=ydata,
                        mode="markers",
                        marker_opacity=0
                    )
                )

        fig.update_xaxes(
                    visible=True,
                    range=[0, (params['naxis2']*scale_factor)]
                )

        fig.update_yaxes(
                    visible=False,
                    range=[0, (params['naxis1']*scale_factor)],
                    # the scaleanchor attribute ensures that the aspect ratio stays constant
                    scaleanchor="x"
                )

        fig.update_layout(
                    images=[go.layout.Image(
                        x=0,
                        sizex=(params['naxis1']*scale_factor),
                        y=(params['naxis2']*scale_factor),
                        sizey=params['naxis2']*scale_factor,
                        xref="x",
                        yref="y",
                        opacity=1.0,
                        layer="below",
                        sizing="stretch",
                        source=image_file)]
                )

        fig.update_layout(
                    width=(params['naxis1']*scale_factor),
                    height=(params['naxis2']*scale_factor),
                    margin={"l": 0, "r": 0, "t": 0, "b": 0},
                )

        return {
            'target': target,
            'plot': offline.plot(fig, output_type='div', show_link=False)
        }

    else:

        plot = '<img src="{% static img/'+str(target.name)+'_colour.png %}" class="img-fluid mx-auto">'

        return {'target': target,
                'plot': plot}
