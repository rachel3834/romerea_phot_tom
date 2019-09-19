from django.shortcuts import render
from django import template
from django import forms
from .forms import TargetNameForm
from tom_targets.models import Target, TargetExtra
from astropy.coordinates import SkyCoord
import astropy.units as u

register = template.Library()

@register.inclusion_tag('custom_views/search.html')
def search(request):

    search_type = 'name'
    rows = ()

    if request.method == "POST":

        nform = TargetNameForm(request.POST)

        if nform.is_valid():

            post = nform.save(commit=False)

            qs = Target.objects.filter(name__contains=post.name)

            rows = render_targetset_as_table_rows(qs)

            print(rows)
            return render(request, 'custom_views/search.html', \
                          {'nform':nform,
                          'message': '',
                          'rows': rows,
                          'search_type': search_type})

    else:

        nform = TargetNameForm()

        return render(request, 'custom_views/search.html', \
                      {'nform':nform,
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
