from __future__ import annotations
from typing import List, Optional
from pathlib import Path
import pandas as pd
import requests

class Fulldata():
    def __init__(self, server, where:dict):
        #
        self._server = server
        self._where = where

        # Create cache directory
        if server.with_cache:
            Path(server.cache_location + "/data").mkdir(parents=True, exist_ok=True)

        # Update list of fulldata
        self._get_fulldata_list()

    def _get_fulldata_list(self):
        # Get fulldata list and description
        query = """query FindManyFullData($where: FullDataWhereInput) {
            findManyFullData(where: $where) {
                id
                description
            }
        }"""
        
        data = {
            "operationName":"FindManyFullData",
            "query": query,
            "variables": {"where": {"TestCampaign": {"Unit": self._where}}}
        }

        fulldata_info = self._server.session().post(self._server.endpoint["graphql"], json = data).json()['data']['findManyFullData']

        self._fulldata_info:dict[dict] = {}
        for fulldata in fulldata_info:
            self._fulldata_info[int(fulldata["id"])] = {
                "description": fulldata["description"],
                "signals": self._get_fulldata_info(int(fulldata["id"]))
            }

        def get_unique_signal_names(signal_data):
            unique_keys = set()
            for nested_dict in signal_data.values():
                unique_keys.update(nested_dict["signals"].keys())
            return list(unique_keys)

        self.fulldata_list = [str(key) for key in self._fulldata_info.keys()]
        self.signal_list = get_unique_signal_names(self._fulldata_info)

    def _get_fulldata_info(self, fulldata_id:int):
        #
        query = """query FindManySignal($where: SignalWhereInput) {
            findManySignal(where: $where) {
                name
                metric
                source
                dataS3Key
            }
        }"""
        
        data = {
            "operationName":"FindManySignal",
            "query": query,
            "variables": {"where": {"FullData": { "id": {"equals": int(fulldata_id)}}}}
        }

        signal_data_list = self._server.session().post(self._server.endpoint["graphql"], json = data, verify=self._server.verify).json()['data']['findManySignal']
        
        signal_data = {}
        for signal in signal_data_list:
            signal_data[signal["name"]] = {
                "metric": signal["metric"],
                "source": signal["source"],
                "dataS3Key": signal["dataS3Key"]
            }

        return signal_data
    
    def dataset(self, fulldata_id:int, signals_list:List[str]) -> Dataset:
        return Dataset(self._server, self._fulldata_info[fulldata_id], signals_list)

    def datasets(self, fulldata_list:Optional[List[int]], signals:List[str]) -> DatasetIterrator:
        """
        Generates datasets for specified signals and fulldata.

        Parameters:
        - fulldata_list (Optional[List[int]]): List of fulldata IDs, default is None.
        - signals (List[str]): List of signal names.

        Returns:
        - DatasetIterator: An iterator over the generated datasets.
        """

        return DatasetIterrator(self, signals, fulldata_list)

class Dataset():
    """
    Represents a dataset with descriptions, signal descriptions, and data.

    Attributes:
    - description: Description of the dataset.
    - signals: Descriptions of signals in the dataset.
    - data: Actual data in the dataset.
    """

    def __init__(self, server, fulldata_info:dict, signals_list:List[str]):
        self.description = fulldata_info["description"]
        self.signal_data = fulldata_info["signals"]
        self._server = server

        signals = {}
        data = []
        for signal_name in signals_list:
            try:
                signal_data, signal_description = self._get_data(self._server.session(), self.signal_data, signal_name)   
                signals[signal_name] = signal_description
                data.append(signal_data)

            except KeyError as e:   
                print(f"{e.args[0]} not found in fulldata")

        if len(data) == 0:
            raise KeyError(f"Fulldata does not contain any of the requested signals. Skipped.")
        
        self.data = pd.concat(data, axis=1)

    def __contains__(self, signal_name):
        return signal_name in self.data.columns
    
    def _get_data(self, session, signal_data, signal_name:str):
        key = signal_data[signal_name]["dataS3Key"]
        cached_data = Path(self._server.cache_location + "/data/" + key.split("/")[-1])
        signal_description = {k: signal_data[signal_name][k] for k in ["metric", "source"]}

        if self._server.with_cache and cached_data.exists():
            signal_data = pd.read_json(cached_data, orient='split', typ='series')

        else:
            file_url = session.get(self._server.endpoint["data"] + "create_test_signal_data_url", params={"keys": key}).json()['data'][key]
            req = requests.get(file_url)

            if req.status_code == 200:
                if self._server.with_cache:
                    with open(cached_data, 'w') as f:
                        f.write(req.text)
                
                signal_data = pd.read_json(req.text, orient='split', typ='series')
                
            else:
                print(f"Server responded with error code {req.status_code}")
                raise TimeoutError("Network error")
            
        return signal_data, signal_description
    
class DatasetIterrator():
    def __init__(self, fulldata:Fulldata, fulldata_list:List[int], signals_list:List[str]):
        self._fulldata = fulldata
        self._fulldata_list = fulldata_list
        self._signals_list = signals_list
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._fulldata_list):
            try:
                dataset = Dataset(self._fulldata._server, self._fulldata._fulldata_info[self._fulldata_list[self._index]], self._signals_list) 
                self._index = self._index + 1
                return dataset
            
            except KeyError as e:  
                print(e)
                self._index = self._index + 1
                return self.__next__()
            
        else:
            raise StopIteration
