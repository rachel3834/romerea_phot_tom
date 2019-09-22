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

            post = form.save(commit=False)

            print('Got HERE')

            if search_type == 'name':
                qs = Target.objects.filter(name__contains=post.name)
                print(qs)

            else:
                radius = post.radius / 3600.0
                qs = Target.objects.filter()

            rows = render_targetset_as_table_rows(qs)

            print(rows)
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
