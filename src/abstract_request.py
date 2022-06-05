# Abstract class(es) to fetch taxonomic databases

from abc import ABC
from abc import abstractmethod

from utils import run_request

# metaclass for requests
class TaxonRequest(ABC):
    '''Abstract class that allows url request for a single taxon.
    '''
    def __init__(self, taxon_id):
        '''Initialize simple request wrapper using taxon ID.
        '''
        self.id = taxon_id
        return

    def run(self, **kwargs):
        '''Submit request and retrieve result.
        '''
        url = self.assemble_request(**kwargs)
        return run_request(url)
    
    @abstractmethod
    def assemble_request(self):
        '''Assemble url for request.
        
        This function needs to be defines in subclasses.
        '''
        return
        
# metaclass for multiple requests
class MultiFetcher(ABC):
    '''Abstract class to do multiple requests at the same time.
    '''
    def __init__(self, taxon_id_or_list):
        '''Initialize from a single taxon ID or a whole list.
        '''
        if isinstance(taxon_id_or_list, list) : self.id_list = taxon_id_or_list
        else : self.id = taxon_id_or_list
        return
    
    @abstractmethod
    def fetch_all(self):
        '''Fetch all taxon IDs for expected data.
        '''
        pass