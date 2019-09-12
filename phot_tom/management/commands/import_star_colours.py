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

    def start_log(self):

        ts = datetime.utcnow()
        log_file = path.join(getcwd(),'data','phot_import_'+ts.strftime("%Y-%m-%d")+'.log')

        log = logging.getLogger( 'phot_import' )

        log.setLevel( logging.INFO )
        file_handler = logging.FileHandler( log_file )
        file_handler.setLevel( logging.INFO )
        formatter = logging.Formatter( fmt='%(asctime)s %(message)s', \
                                    datefmt='%Y-%m-%dT%H:%M:%S' )
        file_handler.setFormatter( formatter )
        log.addHandler( file_handler )

        return log

    def end_log(self, log):

        log.info( 'Processing complete\n' )
        logging.shutdown()

    def check_star_in_tom(self,star_name,log):

        qs = Target.objects.filter(identifier=star_name)

        if len(qs) == 1:
            log.info(' -> Star identified as '+str(qs[0].name))

            return qs[0]
        elif len(qs) > 1:
            raise IOError('Multiple database entries for star '+star_name)
        else:
            return None

    def fetch_stars_from_tom(self,field_name):

        qs = TargetExtra.objects.filter(key='target_type', value='star')

        return qs

    def fetch_star_extras_from_tom(self,star_name):

        qs = TargetExtra.objects.filter(target_name=star_name)

        return qs

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

        return star_keys

    def handle(self, *args, **options):

        verbose = False

        log = self.start_log()

        errors = []

        if not path.isfile(options['phot_db_path']):
            raise IOError('Cannot find photometry database '+options['phot_db_path'])

        conn = phot_db.get_connection(dsn=options['phot_db_path'])

        pri_refimg = import_utils.fetch_primary_reference_image_from_phot_db(conn)
        log.info('Identified primary reference dataset as '+repr(pri_refimg))

        star_colours = import_utils.fetch_star_colours(conn)

        jincr = int(float(len(star_colours))*0.01)

        for j,star_data in enumerate(star_colours):

            star_name = str(options['field_name'])+'-'+str(star_data['star_id'])

            log.info('Processing star '+star_name)

            known_target = self.check_star_in_tom(star_name,log)

            if known_target:

                for key,key_type in self.star_extra_params().items():

                    value = str(star_data[key])

                    TargetExtra.objects.get_or_create(target=known_target, key=key, value=value)

                    log.info('-> '+str(key)+': '+value)
