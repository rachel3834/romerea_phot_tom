"""
Created on Tue Sept 11

@author: rstreet
"""

from django.core.management.base import BaseCommand
from tom_targets.models import Target, TargetExtra
from astropy.coordinates import SkyCoord
from astropy import units as u

class Command(BaseCommand):

    help = 'Imports extra data on the stars of the ROME/REA survey'

    def handle(self, *args, **options):

        targets = Target.objects.all()

        for t in targets[31:]:

            extras = TargetExtra.objects.filter(target=t, key='target_type')

            if len(extras) == 0:

                TargetExtra.objects.create(target=t, key='target_type', value='star')
