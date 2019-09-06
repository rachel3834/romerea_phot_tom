from django.core.management.base import BaseCommand
from tom_targets.models import Target, TargetExtra
from pyDANDIA import phot_db
from os import path, getcwd
from astropy.coordinates import SkyCoord
from astropy import units as u
import logging
from datetime import datetime
from phot_tom.management.commands import import_utils

class Command(BaseCommand):

    help = 'Imports all stars from a pyDANDIA photometric database for a single field'

    def add_arguments(self, parser):
        parser.add_argument('--phot_db_path', help='Path to pyDANDIA photometry database')
        parser.add_argument('--field_name', help='Name of the field')

    def check_arguments(self, options):

        for key in ['phot_db_path', 'field_name']:

            if options[key] == None:
                raise ValueError('Missing argument '+key)

    def start_log(self):

        ts = datetime.utcnow()
        log_file = path.join(getcwd(),'data','star_import_'+ts.strftime("%Y-%m-%d")+'.log')

        log = logging.getLogger( 'star_import' )

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

    def star_extra_params(self):

        star_keys = {'reference_image': 'string',
                     'target_type': 'string',
                     'gaia_source_id': 'string',
                     'gaia_ra': 'float',
                     'gaia_ra_error': 'float',
                     'gaia_dec': 'float',
                     'gaia_dec_error': 'float',
                     'gaia_phot_g_mean_flux': 'float',
                     'gaia_phot_g_mean_flux_error': 'float',
                     'gaia_phot_bp_mean_flux': 'float',
                     'gaia_phot_bp_mean_flux_error': 'float',
                     'gaia_phot_rp_mean_flux': 'float',
                     'gaia_phot_rp_mean_flux_error': 'float',
                     'vphas_source_id': 'string',
                     'vphas_ra': 'float',
                     'vphas_dec': 'float',
                     'vphas_gmag': 'float',
                     'vphas_gmag_error': 'float',
                     'vphas_rmag': 'float',
                     'vphas_rmag_error': 'float',
                     'vphas_imag': 'float',
                     'vphas_imag_error': 'float',
                     'vphas_clean': 'float'}

        return star_keys

    def check_star_in_tom(self,star_name):

        qs = Target.objects.filter(identifier=star_name)

        if len(qs) == 1:
            return qs[0]
        elif len(qs) > 1:
            raise IOError('Multiple database entries for star '+star_name)
        else:
            return None

    def get_target_extra_params(self,target):

        qs = TargetExtra.objects.filter(target=target)

        return qs

    def create_target_extra_with_type(self, target, key, value, key_type):

        if key_type == 'string':
            TargetExtra.objects.create(target=target, key=key, value='"'+str(value)+'"')
        else:
            TargetExtra.objects.create(target=target, key=key, value=value)

    def update_target_extra_with_type(self, target_extra, value, key_type):

        if key_type == 'string':
            target_extra.value = '"'+str(value)+'"'
        else:
            target_extra.value = value
        target_extra.save()

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

        #pri_phot_table = import_utils.fetch_primary_reference_photometry(conn,pri_refimg)

        jincr = int(float(len(stars_table))*0.01)

        for j,star in enumerate(stars_table):

            s = SkyCoord(star['ra'], star['dec'],
                         frame='icrs', unit=(u.deg, u.deg))

            star_name = str(options['field_name'])+'-'+str(star['star_index'])

            base_params = {'identifier': star_name,
                            'name': star_name,
                            'ra': star['ra'],
                            'dec': star['dec'],
                            'galactic_lng': s.galactic.l.deg,
                            'galactic_lat': s.galactic.b.deg,
                            'type': Target.SIDEREAL,
                            }

            log.info('Processing star '+star_name)
            log.info('-> Base parameters:')
            log.info(base_params)

            extra_params = { 'reference_image': pri_refimg['filename'][0],
                             'target_type': 'star' }
            for key,key_type in self.star_extra_params().items():
                if key_type == 'string':
                    extra_params[key] = str(star[key])
                else:
                    extra_params[key] = float(star[key])

            log.info('-> Extra parameters:')
            log.info(extra_params)

            #import pdb;pdb.set_trace()

            known_target = self.check_star_in_tom(star_name)

            log.info('Star in TOM? '+repr(known_target))

            if known_target == None:
                #try:
                target = Target.objects.create(**base_params)
                if verbose: log.info(' -> Created target for star '+star_name)

                for key,key_type in self.star_extra_params().items():

                    value = extra_params[key]

                    if verbose: log.info('Submitting key ',key, value, type(value))

                    self.create_target_extra_with_type(target, key, value, key_type)

                if verbose: log.info(' -> Ingested extra parameters')
                #except OverflowError:
                #    print(base_params,extra_params)
                #    exit()
            else:

                #try:
                if verbose: log.info(' -> '+star_name+' already in database')

                for key, value in base_params.items():
                    setattr(known_target,key,value)
                known_target.save()
                if verbose: log.info(' -> Updated parameters for '+star_name)

                qs = self.get_target_extra_params(known_target)

                if verbose: log.info(' -> Found '+str(len(qs))+' extra parameters for this target')

                for key,key_type in self.star_extra_params().items():

                    value = extra_params[key]

                    for ts in qs:

                        got_key = False

                        if ts.key == key:
                            if verbose: log.info('Submitting key ',key, value, type(value))

                            self.update_target_extra_with_type(ts, value, key_type)

                            got_key = True

                    if not got_key:
                        if verbose: log.info('Adding extra key ',key,value,type(value))
                        self.create_target_extra_with_type(known_target, key, value, key_type)

                if verbose: log.info(' -> Updated extra parameters')
                #except OverflowError:
                #    print(base_params,extra_params)
                #    exit()

            if j%jincr == 0:
                percentage = round((float(j)/float(len(stars_table)))*100.0,0)
                log.info(' -> Ingested '+str(percentage)+\
                            '% complete ('+str(j)+' stars out of '+\
                            str(len(stars_table))+')')
            #import pdb;pdb.set_trace()

        self.end_log(log)
