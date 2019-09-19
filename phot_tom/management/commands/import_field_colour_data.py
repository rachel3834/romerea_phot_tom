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
import numpy as np
from phot_tom.management.commands import import_utils

class Command(BaseCommand):

    help = 'Imports colour photometry data on fields from the ROME/REA survey'

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

    def fetch_or_create_data_product_group(self):

        qs = DataProductGroup.objects.filter(name='romerea')

        if len(qs) == 0:
            group = DataProductGroup(**{'name': 'romerea'})
            group.save()

        else:
            group = qs[0]

        return group

    def check_field_in_tom(self,field_name,log):

        qs = Target.objects.filter(identifier=field_name)

        if len(qs) == 1:
            log.info(' -> Field identified as '+str(qs[0].name))

            return qs[0]
        elif len(qs) > 1:
            raise IOError('Multiple database entries for star '+star_name)
        else:
            return None

    def get_or_create_data_product(self, data_product_params, group):

        qs = DataProduct.objects.filter(product_id=data_product_params['product_id'])

        if len(qs) > 0:
            return qs[0]

        elif len(qs) == 0:
            product = DataProduct.objects.create(**data_product_params)
            product.group.add(group)

            return product

        else:
            raise IOError('Found multiple DataProducts with ID='+data_product_params['product_id'])

    def field_extra_params(self):

        field_keys = {'cal_mag_corr_g': 'g',
                      'cal_mag_corr_g_err': 'gerr',
                      'cal_mag_corr_r': 'r',
                      'cal_mag_corr_r_err': 'rerr',
                      'cal_mag_corr_i': 'i',
                      'cal_mag_corr_i_err': 'ierr',
                      'gi': 'gierr',
                      'gi_err': 'gierr',
                      'gr': 'gr',
                      'gr_err': 'grerr',
                      'ri': 'ri',
                      'ri_err': 'rierr'}

        return field_keys

    def handle(self, *args, **options):

        verbose = False

        log = self.start_log()

        if not path.isfile(options['phot_db_path']):
            raise IOError('Cannot find photometry database '+options['phot_db_path'])

        conn = phot_db.get_connection(dsn=options['phot_db_path'])

        pri_refimg = import_utils.fetch_primary_reference_image_from_phot_db(conn)
        log.info('Identified primary reference dataset as '+repr(pri_refimg))

        ref_image = import_utils.fetch_reference_component_image(conn, pri_refimg['refimg_id'][0])
        log.info('Identified reference image as '+repr(ref_image))

        date_obs = datetime.strptime(ref_image['date_obs_utc'][0],"%Y-%m-%dT%H:%M:%S.%f")
        date_obs = date_obs.replace(tzinfo=pytz.UTC)
        log.info('Reference image timestamp '+date_obs.strftime("%Y-%m-%dT%H:%M:%S.%f"))

        data_source = str(ref_image['facility'][0])+'_'+str(ref_image['filter'][0])
        log.info('Data source code is '+data_source)

        star_colours = import_utils.fetch_star_colours(conn)
        log.info('Extracted colour information for '+str(len(star_colours))+' stars')

        group = self.fetch_or_create_data_product_group()
        log.info('Data product group is '+repr(group))

        field_target = self.check_field_in_tom(options['field_name'],log)
        log.info('Associating with field Target '+repr(field_target))

        field_keys = self.field_extra_params()

        data_array = []
        ns = 0

        for j in range(0, len(star_colours), 1):

            if star_colours['cal_mag_corr_g'][j] > 0.0 or \
                star_colours['cal_mag_corr_r'][j] > 0.0 or \
                    star_colours['cal_mag_corr_i'][j] > 0.0:

                star_data = []

                for key in field_keys.keys():
                    star_data.append(star_colours[key][j])

                data_array.append(star_data)

        data_array = np.array(data_array)

        print('Built data array')

        for i,(key,tag) in enumerate(field_keys.items()):

            if '_err' not in key:

                product_id = options['field_name']+'_pri_ref_'+key
                print('Using product ID='+product_id)

                data_file = path.basename(options['phot_db_path'])+'.'+product_id

                data_product_params = {"product_id": product_id,
                                      "target": field_target,
                                      "observation_record": None,
                                      "data": data_file,  # This is used for uploaded file paths
                                      "extra_data": tag,
                                      "tag": "photometry",
                                      "featured": False,
                                    }

                product = self.get_or_create_data_product(data_product_params, group)

                value = {"magnitude": data_array[:,i].tolist(),
                         "magnitude_error": data_array[:,i+1].tolist(),
                         "filter": tag}

                #value = {}
                #for i,(key,tag) in enumerate(field_keys.items()):
                #    value[key] = data_array[:,i].tolist()
                #value['filter'] = 'gri'

                datum_params = {"target": field_target,
                              "data_product": product,
                              "data_type": "photometry",
                              "source_name": product_id,
                              "source_location": data_source,
                              "timestamp": date_obs,
                              "value": json.dumps(value)}

                print('Composed datum parameters')

                datum = ReducedDatum.objects.create(**datum_params)

                print('Created datum')
