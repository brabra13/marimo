from typing import Callable
import os

from .program import Program

class Labdata:
    """
    Interface to labdata

    Attributes:
    - token (str): Authorization token provided.
    - verify (bool): Do we verify ssl.
    - cache_location (str): Path to the cache folder root.
    - with_cache (bool): Do we enable the cache.
    """

    def __init__(self, token:str, cache_location:str=os.path.dirname(__file__) + "/cache/", with_cache:bool=True) -> None: 
        #
        self.token:str = token
        self.verify:bool = True
        self.cache_location:str = cache_location
        self.with_cache:bool = with_cache

        # endpoint
        self.endpoint:dict[str, str] = {}
        self.endpoint["ipm"] = "https://sfkjhskjf5.execute-api.us-east-1.amazonaws.com/prod/api/"
        self.endpoint["graphql"] = "https://fsghke523.execute-api.eu-west-3.amazonaws.com/prod/graphql"
        self.endpoint["data"] = "https://fglsjkg53sf.execute-api.eu-west-3.amazonaws.com/prod/"
 
        program_url = self.endpoint["ipm"] + "programs?activeFilters=%7B%7D"
        self.program_list = {p['programName']:p['programId'] for p in self.session().get(program_url).json()['programs']}
  
    def program(self, name:str):
        """
        Gets program

        Parameters:
        - name (str): The program name

        Returns:
        - Program: A program instance.
        """
        return Program(name, self)

    def session(self):
        import requests
        from requests.adapters import HTTPAdapter, Retry

        session = requests.Session()
        session.headers = {"Authorization": self.token}
        session.verify = self.verify

        # http_adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[ 403 ]))
        # session.mount('https://emea-labdata-python-prod-rawfiles.s3.amazonaws.com', http_adapter)

        return session
