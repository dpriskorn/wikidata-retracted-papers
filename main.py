# This is a sample Python script.
import logging
from typing import List
from urllib.parse import quote

import requests
import pyalex
from pyalex import Works, Work
from pydantic import BaseModel
from rich.console import Console
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()
instance_of = "P31"
retracted_item = "Q45182324" # see https://www.wikidata.org/wiki/Q45182324
pyalex.config.email = "priskorn@riseup.net"

class Hub(BaseModel):
    doi: str
    found_in_wikidata: bool = False
    qid: str = ""

    def __call_the_hub_api__(self, doi: str = None):
        if doi is None:
            raise ValueError("doi was None")
        if doi == "":
            raise ValueError("doi was empty string")
        url = f"https://hub.toolforge.org/doi:{quote(doi)}?site:wikidata?format=json"
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 302:
            logger.debug("Found QID via Hub")
            self.found_in_wikidata = True
            self.qid = response.headers['Location']
        elif response.status_code == 400:
            self.found_in_wikidata = False
        else:
            logger.error(f"Got {response.status_code} from Hub")
            # console.print(response.json())
            exit()


    def lookup_doi(self) -> None:
        """Lookup via hub.toolforge.org
        It is way faster than WDQS
        https://hub.toolforge.org/doi:10.1111/j.1746-8361.1978.tb01321.x?site:wikidata?format=json"""
        logger.info("Looking up via Hub")
        # if self.doi.found_in_crossref:
        #     doi: str = self.doi.crossref.work.doi
        #     logger.info("Using DOI from Crossref to lookup in Hub")
        #     self.__call_the_hub_api__(doi)
        if not self.found_in_wikidata:
            logger.info("Using DOI to lookup QID via the Hub")
            self.__call_the_hub_api__(self.doi)
            if not self.found_in_wikidata:
                logger.info("Using uppercase DOI to lookup in Hub")
                self.__call_the_hub_api__(self.doi.upper())
                if not self.found_in_wikidata:
                    logger.info("Using lowercase DOI to lookup in Hub")
                    self.__call_the_hub_api__(self.doi.lower())
        logger.info("DOI not found via Hub")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # lookup all retracted papers in OA
    results: List[Work]
    # we want all the ~12k results
    pager = Works().filter(is_retracted=True, has_doi=True).paginate(per_page=2, n_max=None)
    for page in pager:
        # console.print(page)
        for result in page:
            # remove the scheme
            doi = result["doi"].replace("https://doi.org/", "")
            logger.info(f"Working on {doi}")
            # lookup QID
            hub = Hub(doi=doi)
            hub.lookup_doi()
            console.print(hub.dict())
            if hub.found_in_wikidata:
                user_agent = "wikidata-retracted-papers"
                config["user_agent"] = user_agent
                wbi = WikibaseIntegrator()
                paper = wbi.item.get(entity_id=hub.qid.replace("https://www.wikidata.org/wiki/", ""))
                instance_of_claims = paper.claims.get(property=instance_of)
                # console.print(instance_of_claims)
                correctly_marked_as_retracted = False
                for claim in instance_of_claims:
                    # console.print(claim)
                    datavalue = claim.mainsnak.datavalue
                    # console.print(datavalue)
                    if datavalue == retracted_item:
                        correctly_marked_as_retracted = True
                        print("This paper is correctly marked as retracted in Wikidata")
                if not correctly_marked_as_retracted:
                    print(f"This paper is retracted but is missing P31:{retracted_item} in Wikidata, see {hub.qid}")
                # exit()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
