import pandas as pd
import collections
from typing import List

CaptureResult = collections.namedtuple('Captures', ['data', 'metadata'])

class Captures():
    def __init__(self, server, where:dict):
        self._server = server
        self._where = where
        self._value_key_list = ["min", "max", "average", "stdDev"]

    def _parse_capture_values(self, id, values):
        return {key: pd.Series({v["Signal"]["name"]: v[key] for v in values}, name=id) for key in self._value_key_list}    
    
    def _parse_captures(self, captures:List) -> CaptureResult:
        metadata = {}
        data_lists = {k: [] for k in self._value_key_list}

        for capture in captures:
            capture_id = capture["id"]

            # Metadata
            m = {k: v for k, v in capture.items() if k not in ["id", "CaptureValue"]}
            metadata[capture_id] = m

            # Data
            for key, value in self._parse_capture_values(capture_id, capture["CaptureValue"]).items():
                data_lists[key].append(value)

        data = {}
        for key, value in data_lists.items():
            data[key] = pd.concat(data_lists[key], axis=1).T

        return CaptureResult(data, metadata)

    def captures(self) -> CaptureResult:
        #
        query = """query FindManyCapture($where: CaptureWhereInput) {
            findManyCapture(where: $where) {
                id
                startTime
                endTime
                status
                comment
                CaptureValue {
                    average
                    max
                    min
                    stdDev
                    Signal {
                        name
                    }
                }
            }
        }"""
        
        data = {
            "operationName":"FindManyCapture",
            "query": query,
            "variables": {"where": {"FullData": { "TestCampaign": { "Unit": self._where}}}}
        }
    
        captures_data = self._server.session().post(self._server.endpoint["graphql"], json=data).json()['data']['findManyCapture']

        if len(captures_data) > 0:
            return self._parse_captures(captures_data)
        
        else:
            return CaptureResult(None, {})