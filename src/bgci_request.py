# Class(es) to fetch the BCGI databases
# (https://www.bgci.org/resources/bgci-databases/)

import arrow
from io import StringIO
import os
import pandas as pd

from abstract_request import TaxonRequest
from abstract_request import MultiFetcher

from utils import init_csvwriter

class BGCIRequest(TaxonRequest):
    '''Class that allows to obtain information about ex sit collections of specific taxa.
    '''
    def __init__(self, genus="", species="", epithet=""):
        '''Initialize request wrapper using genus, species and epithet name
        '''
        self.genus = genus
        self.species = species
        self.epithet = epithet
        return
    
    def assemble_request(self):
        '''Assemble url for request.
        '''
        url = (f'https://tools.bgci.org/plant_search.php?ftrFamily=&ftrExcludeCultivar=Y&ftrRedList=&ftrGenus={self.genus}'
               f'&ftrRedList1997=&ftrSpecies={self.species}&ftrEpithet={self.epithet}&ftrGardenID=&ftrPagerLimit=100000&'
               'ftrCWR=&ftrMedicinal=&ftrNewZealand=&ftrMexico=&ftrCITES=&ftrTCD=&ftrGTC=&action=Find&export=1')
        return url
    
    def get_collection_data(self, include_all_subspecies=True):
        '''Retrieve collection data from BCGI for taxon.
        '''
        df = pd.read_csv(StringIO(self.run()))

        for key, val in zip(["Genus", "Species", "Infraspecific Epithet"],
                            [self.genus, self.species, self.epithet]):
            if val == "":
                if key != "Infraspecific Epithet" or not include_all_subspecies:
                    df = df[df[key].isna()]
            else:
                df = df[df[key].str.lower() == val.lower()]
        return df
# end BGCIRequest
    
class BGCIFromEuroMedMultiFetcher(MultiFetcher):
    '''Class that allows to fetch all taxa from an euro+med fetch.
    '''
    def __init__(self, euromed_csvfile):
        '''Initialize wrapper from euro+med plant csv file.
        '''
        self.df = pd.read_csv(euromed_csvfile)
        return
        
    def fetch_all(self, csv_file, include_all_subspecies=False, level="species", force=False):
        '''Document all found species in collections in csv file.
        '''
        # columns for our csv file
        HEADER = {"bgci_id": 'ID',
                  "hybrid_genus": 'Genus Hybrid',
                  "genus": 'Genus',
                  "hybrid_species": 'Species Hybrid',
                  "species": 'Species',
                  "epithet_rank": 'Infraspecific Rank',
                  "epithet": 'Infraspecific Epithet',
                  "status": 'Status',
                  "n_collections": 'No. of ex situ sites worldwide',
                  "iucn_red_list": 'IUCN Red List',
                  "iucn_red_list_1997": 'IUCN Red List 1997',
                  "cites": 'CITES Appendix',
                  "euro_med_id": None,
                  "date_fetched": None}
        old_header = [v for v in HEADER.values() if v is not None]
        
        # lambda for handyness
        buffer_key = lambda dct, k : "" if k not in dct.keys() else dct[k]
        
        # intialize csv
        file_handle, csv_writer = init_csvwriter(csv_file, HEADER.keys(), force=force)
        
        # get all necessary taxa 
        if level == "species":
            df = self.df[self.df['Subspecies'].isna()]
            taxon_lvl = "Species"
        elif level == "subspecies":
            df = self.df
            taxon_lvl = "Subspecies"
        else: raise RuntimeError(f"Wrong level selected: {level}; choose 'species' or 'subsoecies'.")

        # start the requests
        for j, taxon_row in df.loc[~df[taxon_lvl].isna()].iterrows():
            taxon = taxon_row[taxon_lvl].split(" ")
            if level == "species":
                bgcir = BGCIRequest(genus=taxon[0], species=taxon[1])
            else:
                bgcir = BGCIRequest(genus=taxon[0], species=taxon[1], epithet=taxon[2])
            
            # load the data
            coll_df = bgcir.get_collection_data()
            coll_df = coll_df.loc[:, old_header]
            
            # store it
            for i, row in coll_df.iterrows():
                csv_row_dict = {
                    **{k: row[ok] for k, ok in HEADER.items() if ok is not None},
                    "euro_med_id": taxon_row["euro_med_id"],
                    "date_fetched": str(arrow.now())
                }
                csv_writer.writerow(csv_row_dict)
            file_handle.flush()
            
        # termination
        file_handle.close()
        return
# end BGCIFromEuroMedMultiFetcher