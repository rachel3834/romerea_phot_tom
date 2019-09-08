"""
Created on Sat Sept 7

@author: rstreet
"""

from django.core.management.base import BaseCommand
from tom_targets.models import Target, TargetExtra
from tom_dataproducts.models import ReducedDatum, DataProductGroup, DataProduct
from astropy.coordinates import SkyCoord
from astropy import units as u
from pyDANDIA import phot_db
from os import path, getcwd
from datetime import datetime
import pytz
import json
import logging
from phot_tom.management.commands import import_utils

class Command(BaseCommand):

    help = 'Imports colour photometry data on stars from the ROME/REA survey'

    def add_arguments(self, parser):
        parser.add_argument('--phot_db_path', help='Path to pyDANDIA photometry database')
        parser.add_argument('--field_name', help='Name of the field')

    def check_star_in_tom(self,star_name):

        qs = Target.objects.filter(identifier=star_name)

        if len(qs) == 1:
            return qs[0]
        elif len(qs) > 1:
            raise IOError('Multiple database entries for star '+star_name)
        else:
            return None

    def star_extra_params(self):

        star_keys = {'cal_mag_corr_g': 'float',
                    'cal_mag_corr_g_err': 'float',
                    'cal_mag_corr_r': 'float',
                    'cal_mag_corr_r_err': 'float',
                    'cal_mag_corr_i': 'float',
                    'cal_mag_corr_i_err': 'float',
                    'gi': 'float',
                    'gi_err': 'float',
                    'gr': 'float',
                    'gr_err': 'float',
                    'ri': 'float',
                    'ri_err': 'float'}

    def handle(self, *args, **options):

        verbose = False

        self.check_arguments(options)

        log = self.start_log()

        errors = []

        if not path.isfile(options['phot_db_path']):
            raise IOError('Cannot find photometry database '+options['phot_db_path'])

        conn = phot_db.get_connection(dsn=options['phot_db_path'])

        pri_refimg = import_utils.fetch_primary_reference_image_from_phot_db(conn)
        log.info('Identified primary reference dataset as '+repr(pri_refimg))

        stars_table = import_utils.fetch_starlist_from_phot_db(conn,pri_refimg,log)

        star_colours = import_utils.fetch_star_colours(conn)

        jincr = int(float(len(stars_table))*0.01)

        for j,star in enumerate(stars_table):

            star_name = str(options['field_name'])+'-'+str(star['star_index'])

            log.info('Processing star '+star_name)

            known_target = self.check_star_in_tom(star_name)

            extra_params = {}
            
            for key,key_type in self.star_extra_params().items():
                if key_type == 'string':
                    extra_params[key] = str(star[key])
                else:
                    extra_params[key] = float(star[key])

            log.info('-> Extra parameters:')
            log.info(extra_params)
