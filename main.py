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

from doi import Doi

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
console = Console()
instance_of = "P31"
retracted_item = "Q45182324"  # see https://www.wikidata.org/wiki/Q45182324
pyalex.config.email = "priskorn@riseup.net"


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    user_agent = "wikidata-retracted-papers"
    config["USER_AGENT"] = user_agent
    wbi = WikibaseIntegrator()
    # lookup all retracted papers in OA
    results: List[Work]
    # we want all the ~12k results
    pager = Works().filter(is_retracted=True, has_doi=True).paginate(per_page=2, n_max=None)
    count_missing_retraction_in_wd = 0
    count = 1
    for page in pager:
        # console.print(page)
        for result in page:
            console.print(f"Count: {count}, "
                          f"missing retraction in WD: {count_missing_retraction_in_wd} "
                          f"({round(count_missing_retraction_in_wd/count)}%)")
            # remove the scheme
            doi_string = result["doi"].replace("https://doi.org/", "")
            logger.info(f"Working on {doi_string}")
            # lookup QID
            doi_model = Doi(doi=doi_string)
            doi_model.lookup_doi()
            if doi_model.marked_as_retracted_in_openalex and not doi_model.marked_as_retracted_in_wikidata:
                count_missing_retraction_in_wd += 1
            count += 1

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
