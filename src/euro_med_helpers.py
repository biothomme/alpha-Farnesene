# Here we include functionalities that help to access information from euro med database
import json
import re

class DistributionString:
    '''Class that helps to decode the euro med distribution string.
    '''
    # static import
    EUROMED_COUNTRY_FILE = "../cache/euromed_countries.json"
    try:
        ALL_COUNTRIES = json.load(open(EUROMED_COUNTRY_FILE, "r"))
    except FileNotFoundError:
        ALL_COUNTRIES = json.load(open(f'../{EUROMED_COUNTRY_FILE}', "r"))
    
    # core
    def __init__(self, html_string):
        '''Initialize from HTML string of distribution of euro med page.
        '''
        # all native regions:
        html_rest = self.get_natives(html_string)
        
        # all introduced regions:
        html_rest = self.get_introduced(html_rest)
        
        # for non-natives we take the remaining string
        self.non_native_str = html_rest.strip()
        
        # in a next step we go in more detail
        # we do not take subregions into account
        self.remove_subregions()
        
        return
    
    def get_natives(self, html_string):
        '''Obtain native regions for plant given its html_string.
        '''
        # first, we check if plant is endemic (annotated with ●)
        if "●" in html_string:
            self.endemic = True
            html_string = html_string.replace("●", "").strip()
        else:
            self.endemic = False

        # native regions are bold
        natives = re.findall("\<b\>([^\<\>]*)\<\/b\>", html_string)
        
        # for hits, we use concatenate them again
        if natives:
            self.native_str = " ".join(natives).strip()
            html_string = html_string.replace("<b>", "").replace("</b>", "")
            for native in natives:
                html_string = html_string.replace(native, "")
        else:
            self.native_str = ""
            
        return html_string
    
    
    def get_introduced(self, html_string):
        '''Obtain introduced regions for plant given its html_string.
        '''
        # native regions are bold
        introduced = re.findall("\[([^\<\>]*)\]", html_string)
        
        # for hits, we use concatenate them again
        if introduced:
            self.introduced_str = " ".join(introduced).strip()
            html_string = html_string.replace("[", "").replace("]", "")
            for introduce in introduced:
                html_string = html_string.replace(introduce, "")
        else:
            self.introduced_str = ""
        return html_string
    
    def remove_subregions(self):
        '''Delete subregions from native/non-native strings.
        '''
        # simply we rplace all characters that are in bracktes by nothing
        SUBREG_REGEX = "\([^\(\)]*\)"
        self.native_str = re.sub(SUBREG_REGEX, "", self.native_str)
        self.introduced_str = re.sub(SUBREG_REGEX, "", self.introduced_str)
        self.non_native_str = re.sub(SUBREG_REGEX, "", self.non_native_str)
        return
    
    def summarize(self):
        '''Summarize occurence for all regions of euro+med.
        '''
        self.occurence = {key: "missing" for key in DistributionString.ALL_COUNTRIES.keys()}
        
        # load the native/endemic occurences
        self.load_natives()
        
        # load introduced occurences
        self.load_introduceds()
        
        # load special distribution status
        self.load_rest()
        
        old_keys = list(self.occurence.keys())
        [self.occurence.pop(key) for key in old_keys if key not in DistributionString.ALL_COUNTRIES.keys()]
        return self.occurence
    
    def load_natives(self):
        '''Document the regions, where species is native/endemic.
        '''
        if self.endemic : status = "endemic"
        else : status = "native"
        
        for country in self.native_str.split(" "):
            if country == "" : continue
            self.occurence[country] = status
        return
    
    def load_introduceds(self):
        '''Document the regions, where species is introduced.
        '''
        for country in self.introduced_str.split(" "):
            if country == "" : continue
            elif country.startswith("a"):
                self.occurence[country[1:]] = "casual alien"
            elif country.startswith("a"):
                self.occurence[country[1:]] = "casual alien"
            elif country.startswith("c"):
                self.occurence[country[1:]] = "cultivated"
            elif country.startswith("n"):
                self.occurence[country[1:]] = "naturalized"
            elif country in DistributionString.ALL_COUNTRIES.keys():
                self.occurence[country] = "introduced"
        return
    
    def load_rest(self):
        '''Document the regions, where species is documented but not native or introduced.
        '''
        for country in self.non_native_str.split(" "):
            if country == "" : continue
            elif country.startswith("-"):
                self.occurence[country[1:]] = "absent but reported in error"
            elif country.startswith("?"):
                self.occurence[country[1:]] = "doubtfully present"
            elif country.startswith("d"):
                self.occurence[country[1:]] = "doubtfully native"
            elif country.startswith("†"):
                self.occurence[country[1:]] = "presumably extinct"
            elif country in DistributionString.ALL_COUNTRIES.keys():
                self.occurence[country] = "undefined"
        return
# end DistributionString