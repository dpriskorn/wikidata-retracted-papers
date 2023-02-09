# This is a sample Python script.
import logging
from typing import List
from urllib.parse import quote

import requests
from pyalex import Works, Work
from pydantic import BaseModel
from rich.console import Console

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
console = Console()

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
            console.print(response.json())
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
    results, meta = Works().filter(is_retracted=True, has_doi=True).get(return_meta=True)
    for result in results:
        doi = result["doi"]
        logger.info(f"Working on {doi}")
        # lookup QID
        hub = Hub(doi=doi)
        hub.lookup_doi()
        console.print(hub.dict())
        exit()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
