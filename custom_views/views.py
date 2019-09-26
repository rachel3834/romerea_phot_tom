from django.shortcuts import render
from django import template
from django import forms
from .forms import TargetNameForm, TargetPositionForm
from tom_targets.models import Target, TargetExtra
from astropy.coordinates import SkyCoord
import astropy.units as u

register = template.Library()

@register.inclusion_tag('custom_views/search.html')
def search(request,search_type='name'):

    rows = ()

    if request.method == "POST":

        if search_type=='name':
            form = TargetNameForm(request.POST)
        else:
            form = TargetPositionForm(request.POST)

        if form.is_valid():

            if search_type == 'name':

                post = form.save(commit=False)

                qs = Target.objects.filter(name__contains=post.name)

            else:

                params = {}
                for key, value in form.cleaned_data.items():
                    params[key] = value

                cone_radius = params['radius'] / 3600.0
                qs = cone_search(params['ra'], params['dec'], cone_radius)

            rows = render_targetset_as_table_rows(qs)

            return render(request, 'custom_views/search.html', \
                          {'form':form,
                          'message': '',
                          'rows': rows,
                          'search_type': search_type})

    else:


        if search_type=='name':
            form = TargetNameForm()
        else:
            form = TargetPositionForm()

        return render(request, 'custom_views/search.html', \
                      {'form':form,
                      'message': '',
                      'rows': rows,
                      'search_type': search_type})

def render_targetset_as_table_rows(qs):

    pks = []
    names = []
    ras = []
    decs = []

    for entry in qs:
        s = SkyCoord(ra=float(entry.ra)*u.deg, dec=float(entry.dec)*u.deg, frame='icrs')
        pks.append(entry.pk)
        names.append(entry.name)
        ras.append(s.ra.to_string(u.hour,sep=':'))
        decs.append(s.dec.to_string(u.deg,sep=':'))

    rows = zip(pks, names, ras, decs)
    rows = sorted(rows, key=lambda row: row[1])

    return rows

def cone_search(ra_centre, dec_centre, cone_radius):
    """RA, Dec and radius should be in decimal degrees"""

    ra_centre = float(ra_centre)
    dec_centre = float(dec_centre)

    centre = SkyCoord(ra=ra_centre*u.deg, dec=dec_centre*u.deg, frame='icrs')

    ra_min = ra_centre - cone_radius
    ra_max = ra_centre + cone_radius
    dec_min = dec_centre - cone_radius
    dec_max = dec_centre + cone_radius

    qs = Target.objects.filter(ra__gte=ra_min, ra__lte=ra_max,
                                dec__gte=dec_min, dec__lte=dec_max)
    results = []

    for star in qs:

        s = SkyCoord(ra=float(star.ra)*u.deg, dec=float(star.dec)*u.deg, frame='icrs')

        sep = centre.separation(s)

        if sep.degree <= cone_radius:
            results.append(star)

    return results
