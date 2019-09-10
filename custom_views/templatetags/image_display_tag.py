import json

from django import template
from django.core.paginator import Paginator
from datetime import datetime

from plotly import offline
import plotly.graph_objs as go
from astropy.coordinates import SkyCoord

register = template.Library()

@register.inclusion_tag('custom_views/image_display.html')
def navigable_image(target, file_path):
    #photometry_data = {}
    #for datum in ReducedDatum.objects.filter(target=target, data_type=PHOTOMETRY[0]):
    #    values = json.loads(datum.value)
    #    photometry_data.setdefault(values['filter'], {})
    #    photometry_data[values['filter']].setdefault('time', []).append(datum.timestamp)
    #    photometry_data[values['filter']].setdefault('magnitude', []).append(values.get('magnitude'))
    #    photometry_data[values['filter']].setdefault('error', []).append(values.get('error'))

    half_width = (targets_extras.npixels/2.0) * targets_extras.pixscale

    xdata = np.arange(target.ra-half_width,target.ra+half_width,0.25)
    ydata = np.arange(target.dec-half_width,target.dec+half_width,0.25)

    plot_data = [
        go.Scatter(
            x=xdata,
            y=ydata,
        ) ]
    layout = go.Layout.Image(
            source=file_path,
            xref="x",
            yref="y",
            x=0,
            y=3,
            sizex=2,
            sizey=2,
            sizing="stretch",
            opacity=0.5,
            layer="below")

    return {
        'target': target,
        'plot': offline.plot(go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False)
    }
