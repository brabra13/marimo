import os
import requests
import httpx
import json # Import json module for potential JSONDecodeError
from requests.exceptions import JSONDecodeError # More specific exception
from .program import Program # Assuming program.py is in the same directory or install path

class Labdata:
    """
    Interface to labdata

    Attributes:
    - token (str): Authorization token provided.
    - verify (bool): Do we verify ssl.
    - cache_location (str): Path to the cache folder root.
    - with_cache (bool): Do we enable the cache.
    """

    def __init__(self, token:str, cache_location:str=None, with_cache:bool=True) -> None:
        self.token:str = token
        self.verify:bool = True # Consider making this configurable if needed

        # Default cache location relative to this file
        if cache_location is None:
            # Ensure the directory exists
            default_cache_dir = os.path.join(os.path.dirname(__file__), "cache")
            os.makedirs(default_cache_dir, exist_ok=True)
            self.cache_location:str = default_cache_dir
        else:
             self.cache_location:str = cache_location
             os.makedirs(self.cache_location, exist_ok=True) # Ensure custom location exists too

        self.with_cache:bool = with_cache
        self.program_list = {} # Initialize as empty
        self._initialized = False # Flag to track initializatio

        # endpoint
        self.endpoint:dict[str, str] = {}
        self.endpoint["ipm"] = "https://se6gxc1ez0.execute-api.us-east-1.amazonaws.com/prod/api/"
        self.endpoint["graphql"] = "https://5mdo3qfkzd.execute-api.eu-west-3.amazonaws.com/prod/graphql"
        self.endpoint["data"] = "https://ra7m85hap8.execute-api.eu-west-3.amazonaws.com/prod/"



    # Provide an async method to fetch initial data
    async def initialize(self):
        if self._initialized:
            return # Don't initialize twice
        
        program_url = self.endpoint["ipm"] + "programs?activeFilters=%7B%7D"
        print(f"Initializing Labdata: Requesting programs from {program_url}") # Use print or logging

        print(f"Requesting programs from: {program_url}")
        try:
            async with httpx.AsyncClient(verify=self.verify, timeout=60.0) as client:
                headers = {"Authorization": self.token}
                response = await client.get(program_url, headers=headers)

            print(f"--- API Response ---") # Use print or logging
            print(f"Status Code: {response.status_code}")
            print(f"Received Bytes: {len(response.content)}")

            response.raise_for_status() # Raise HTTPError for bad responses

            json_data = response.json()

            print("JSON Parsed Successfully.")
            if isinstance(json_data, dict) and 'programs' in json_data:
                self.program_list = {p['programName']:p['programId'] for p in json_data['programs']}
                print(f"Successfully populated program_list with {len(self.program_list)} items.")
            else:
                print("ERROR: Unexpected JSON structure.")
                self.program_list = {}

            self._initialized = True

        except httpx.RequestError as e:
            print(f"ERROR: Request failed during initialization: {e}")
            self.program_list = {}
        except json.JSONDecodeError as e:
             print(f"ERROR: Failed to decode JSON during initialization: {e}")
             self.program_list = {}
        except Exception as e:
            print(f"ERROR: An unexpected error occurred during initialization: {e}")
            self.program_list = {}

        # --- REMOVED REDUNDANT CALL ---
        # This line was removed because the call is already made inside the try block
        # self.program_list = {p['programName']:p['programId'] for p in self.session().get(program_url).json()['programs']}


    # Make other methods that need the session async
    async def get_response_data(self):
        if not self._initialized:
             await self.initialize() # Ensure initialized

        program_url = self.endpoint["ipm"] + "programs?activeFilters=%7B%7D"
        # Simplified example, add full error handling like in initialize
        async with httpx.AsyncClient(verify=self.verify, timeout=60.0) as client:
             headers = {"Authorization": self.token}
             response = await client.get(program_url, headers=headers)
             response.raise_for_status()
             return response.json()


    def program(self, name:str):
        """
        Gets program

        Parameters:
        - name (str): The program name

        Returns:
        - Program: A program instance.
        """
        # Ensure Program class is accessible
        try:
             from .program import Program
        except ImportError:
             # Handle case where program.py might not be found relative
             # This depends highly on your project structure
             print("Warning: Could not import Program relative. Trying direct import.")
             try:
                 import program # Assuming program.py is in PYTHONPATH
                 Program = program.Program
             except ImportError:
                  print("Error: Failed to import Program class.")
                  return None # Or raise an error

        if name not in self.program_list:
            print(f"Warning: Program '{name}' not found in initialized list. Available: {list(self.program_list.keys())}")
            # Decide if you want to return None, raise error, or try fetching again
            return None # Example: return None

        program_id = self.program_list[name]
        # Assuming Program constructor takes name, id, and the Labdata instance
        return Program(name, program_id, self)


    def session(self):
        # import requests # Already imported at the top
        # from requests.adapters import HTTPAdapter, Retry # Keep if using retries

        session = requests.Session()
        session.headers = {"Authorization": self.token}
        session.verify = self.verify

        # Retries are often useful, uncomment if needed, but won't fix JSON errors
        # http_adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])) # Retry on server errors
        # session.mount('https://', http_adapter) # Mount for all https

        return session