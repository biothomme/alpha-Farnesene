# Class(es) to fetch the IUCN red list database using its api
# (https://apiv3.iucnredlist.org/api/v3/docs)

import arrow
from io import StringIO
import json
import os
import pandas as pd

from abstract_request import TaxonRequest
from abstract_request import MultiFetcher

from utils import init_csvwriter

class RedListRequest(TaxonRequest):
    '''Class that allows to obtain information about red list status of specific taxa.
    '''
    def __init__(self, genus="", species="", token="9bb4facb6d23f48efbf424bb05c0c1ef1cf6f468393bc745d42179ac4aca5fee"):
        '''Initialize request wrapper using genus, species and epithet name
        '''
        self.genus = genus
        self.species = species
        
        self.token = token
        return
    
    def assemble_request(self, request_type="summary"):
        '''Assemble url for request.
        '''
        if request_type == "summary":
            url = (f'https://apiv3.iucnredlist.org/api/v3/species/{self.genus}%20{self.species}?token={self.token}')
        elif request_type == "habitat":
            url = (f'https://apiv3.iucnredlist.org/api/v3/habitats/species/name/{self.genus}%20{self.species}?token={self.token}')
        elif request_type == "threat":
            url = (f'https://apiv3.iucnredlist.org/api/v3/threats/species/name/{self.genus}%20{self.species}?token={self.token}')
        return url
# end RedListRequest
    
class RedListMultiFetcher(MultiFetcher):
    '''Class that allows to fetch all taxa of euromed+bgci fetch against IUCN red list.
    '''
    def __init__(self, euromed_csvfile, bgci_csvfile):
        '''Initialize wrapper from euro+med plant csv file.
        '''
        euromed_df = pd.read_csv(euromed_csvfile)
        bgci_df = pd.read_csv(bgci_csvfile)
        
        # to obtain the species listed in BGCI, we merge both dataframes
        # and only take the unique rows of it
        cultivated_plants_df = euromed_df.merge(bgci_df, on="euro_med_id", how="inner").loc[:,["genus", "species", "euro_med_id"]]

        cultivated_plants_df["genus"] = cultivated_plants_df["genus"].str.lower()
        cultivated_plants_df["species"] = cultivated_plants_df["species"].str.lower()

        cultivated_plants_df.drop_duplicates(inplace=True)
        
        self.df = cultivated_plants_df
        return
    
    
    def fetch_all(self, csv_file, force=False):
        '''Document all found species in collections in csv file.
        '''
        # columns for our csv file
        HEADER = ["euro_med_id",
                  "date_fetched",
                  'taxonid',
                  'scientific_name',
                  'kingdom',
                  'phylum',
                  'class',
                  'order',
                  'family',
                  'genus',
                  'main_common_name',
                  'authority',
                  'published_year',
                  'assessment_date',
                  'category',
                  'criteria',
                  'population_trend',
                  'marine_system',
                  'freshwater_system',
                  'terrestrial_system',
                  'assessor',
                  'reviewer',
                  'aoo_km2',
                  'eoo_km2',
                  'elevation_upper',
                  'elevation_lower',
                  'depth_upper',
                  'depth_lower',
                  'errata_flag',
                  'errata_reason',
                  'amended_flag',
                  'amended_reason']
        
        # lambda for handyness
        buffer_key = lambda dct, k : "" if k not in dct.keys() else dct[k]
        
        # intialize csv
        file_handle, csv_writer = init_csvwriter(csv_file, HEADER, force=force)
        
        # start the requests
        for i, plant_data in self.df.iterrows():
            print(i, end=" ")
            rlr = RedListRequest(genus=plant_data["genus"], species=plant_data["species"])
            result = json.load(StringIO(rlr.run()))
            if "result" in result.keys():
                if len(result["result"]) > 0:
                    csv_row_dict = {
                        "euro_med_id": plant_data["euro_med_id"],
                        "date_fetched": str(arrow.now()),
                        **result["result"][0]
                    }
                    csv_writer.writerow(csv_row_dict)
                    file_handle.flush()
            
        # termination
        file_handle.close()
        return
# end BGCIFromEuroMedMultiFetcher