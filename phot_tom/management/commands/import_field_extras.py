"""
Created on Tue Jul 23 11:01:54 2019

@author: rstreet
"""

from django.core.management.base import BaseCommand
from tom_targets.models import Target, TargetExtra
from astropy.coordinates import SkyCoord
from astropy import units as u

class Command(BaseCommand):

    help = 'Imports data on the target fields of the ROME/REA survey'

    def add_arguments(self, parser):
        parser.add_argument('--field_name', help='Name of the field')
        parser.add_argument('--pixscale', help='CCD pixel scale [arcsec/pixel]')
        parser.add_argument('--naxis1', help='Reference image NAXIS1 [pixels]')
        parser.add_argument('--naxis2', help='Reference image NAXIS2 [pixels]')

    def check_field_in_tom(self,field_id):

        qs = Target.objects.filter(identifier=str(field_id))

        if len(qs) == 1:
            return qs[0]
        elif len(qs) > 1:
            raise IOError('Multiple database entries for star '+field_id)
        else:
            return None

    def check_stars_in_field(self,field_id):

        qs = Target.objects.filter(name__contains=field_id)

        return len(qs)

    def handle(self, *args, **options):

        field = self.check_field_in_tom(options['field_name'])

        if field != None:

            nstars = self.check_stars_in_field(options['field_name'])

            print(' -> Found '+str(nstars)+' stars in field '+options['field_name'])

            TargetExtra.objects.create(target=field, key='nstars', value=str(nstars))
            TargetExtra.objects.create(target=field, key='pixscale', value=str(options['pixscale']))
            TargetExtra.objects.create(target=field, key='naxis1', value=str(options['naxis1']))
            TargetExtra.objects.create(target=field, key='naxis2', value=str(options['naxis2']))

            print(' -> Ingested information for field '+options['field_name'])

        else:

            raise IOError('Field '+options['field_name']+' not found in database')
