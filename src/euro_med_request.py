# Class(es) to fetch the Euro+Med PlantBase
# (https://www.emplantbase.org/home.html)

import arrow
import csv
from io import StringIO
import json
import os
import pandas as pd
import re

from abstract_request import TaxonRequest
from abstract_request import MultiFetcher

from utils import init_csvwriter


class EuroMedSpeciesRequest(TaxonRequest):
    '''Class to fetch euro+med plantbase with a single taxon ID.
    '''
    def assemble_request(self):
        '''Assemble url for request.
        '''
        url = f"https://api.cybertaxonomy.org/euromed/portal/classification/314a68f9-8449-495a-91c2-92fde8bcf344/childNodesOf/{self.id}"
        return url
    
    def collect_phylogeny(self, taxon_status="Unknown", **kwargs):
        '''Collect the total phylogeny of all children of given parent taxid.
        '''
        phylogeny = {**kwargs}
        children_info = json.load(StringIO(self.run()))
        
        # some entries have no children (e.g. species)
        if len(children_info) == 0:
            important_info = {
                **phylogeny,
                "taxon_status": taxon_status,
                "euro_med_id": self.id,
                "date_fetched": str(arrow.now())
            }
            yield important_info
        
        # others are internal nodes, those we do not need, but we recursivley run the function
        for child in children_info:
            phylogeny[child["rankLabel"]] = child["nameCache"]
            
            child_emsr = EuroMedSpeciesRequest(child["taxonUuid"])
            # 'YIELD FROM' IS MAGIC!
            yield from child_emsr.collect_phylogeny(taxon_status=child["taxonStatus"], **phylogeny)
        return
    
class EuroMedSpeciesFetcher(MultiFetcher):
    '''Class to fetch all species of the euro+med plantbase.
    '''
    def fetch_all(self, csv_file, force=False, extend=True):
        '''Fetch all species/subsp. from the plantbase.
        '''
        # columns for our csv file
        HEADER = ['Division',
                  'Subdivision',
                  'Class',
                  'Subclass',
                  'Superorder',
                  'Order',
                  'Family',
                  'Genus',
                  'Species',
                  'Subspecies',
                  'taxon_status',
                  'euro_med_id',
                  'date_fetched']
        # taxid for plants
        BASAL_TAXID = "4a889e6c-9816-4745-9d06-146969da30c0"
        
        # lambda for handyness
        buffer_key = lambda dct, k : "" if k not in dct.keys() else dct[k]
        
        # intialize csv
        file_handle, csv_writer = init_csvwriter(csv_file, HEADER, force=force, extend=extend)
        
        # start the requests
        emsr = EuroMedSpeciesRequest(BASAL_TAXID)
        
        for tax_data in emsr.collect_phylogeny():
            csv_writer.writerow(
                {k: buffer_key(tax_data, k) for k in HEADER}
            )
            file_handle.flush()
            
        # termination
        file_handle.close()
        return
# end EuroMedSpeciesFetcher


class EuroMedDistributionRequest(TaxonRequest):
    '''Class to fetch euro+med plantbase for distributions given an euro med ID.
    '''
    def assemble_request(self):
        '''Assemble url for request.
        '''
        url = f"https://europlusmed.org/cdm_dataportal/taxon/{self.id}"
        return url
    
    def collect_locations(self):
        '''Collect the total phylogeny of all children of given parent taxid.
        '''
        whole_info = StringIO(self.run())
        
        return whole_info
    
    def run(self, **kwargs):
        '''Submit request and retrieve result.
        '''
        from utils import run_request_sneaky
        url = self.assemble_request(**kwargs)
        return run_request_sneaky(url)
# end EuroMedDistributionRequest

class EuroMedDistributionFetcher(MultiFetcher):
    '''Class to fetch distributions of multiple species within the euro+med plantbase.
    '''
    def __init__(self, euromed_csvfile):
        '''Initialize wrapper from csv file that lists euromed_ids.
        '''
        self.df = pd.read_csv(euromed_csvfile)
        return
    
    def fetch_all(self, csv_file, force=False, extend=True, skip_existing=True):
        '''Fetch all species/subsp. from the plantbase.
        '''
        from euro_med_helpers import DistributionString
        # columns for our csv file
        HEADER = ["euro_med_id",
                  "date_fetched",
                  *DistributionString.ALL_COUNTRIES.keys()]
        
        # extend only neccessary
        if os.path.exists(csv_file) and extend and skip_existing:
            fetched_ids = pd.read_csv(csv_file)["euro_med_id"].unique()
            print(fetched_ids)
        else:
            fetched_ids = []
        
        # intialize csv
        file_handle, csv_writer = init_csvwriter(csv_file, HEADER, force=force, extend=extend)
        
        # start the requests
        for em_id in self.df["euro_med_id"].unique():
            if em_id in fetched_ids:
                print(em_id)
                continue
            
            emdr = EuroMedDistributionRequest(em_id)
            
            try:
                dist_row = [row for row in emdr.collect_locations().readlines() if row.strip().startswith('<div id="openlayers-container-distribution')][0]
                dist_str = dist_row.split('<p class="condensed_distribution">')[1].split("&nbsp;")[0]
            
                csv_row = {"euro_med_id": em_id,
                       "date_fetched": str(arrow.now()),
                       **DistributionString(dist_str).summarize()}
            except IndexError:
                continue
            else:
                csv_writer.writerow(csv_row)
                file_handle.flush()
            
        # termination
        file_handle.close()
        return
# end EuroMedSpeciesFetcher