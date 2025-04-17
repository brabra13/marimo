from __future__ import annotations
from typing import List, Optional

from .fulldata import Fulldata
from .captures import Captures

class Program():
    """
    Represents a program with units and related functionality.

    Attributes:
    - name (str): The name of the program.
    - server: The server instance used for communication.

    Example:
    ```python
    authorization_header = "Bearer eyJhbGcxxxxxx..."
    labdata = Labdata(authorization_header)
    zenith = labdata.program("Zenith")
    ecs1 = zenith.unit("ecs1")
    ```
    """

    def __init__(self, id:int, server) -> None: 
        #
        self._server = server

        # Program information
        self.id = id
        self._where = {"TestCampaign": {"some": {"programId": {"equals": int(self.id)}}}}
      
        # List all units
        query = """query FindManyUnit($where: UnitWhereInput) {
            findManyUnit(where: $where) {
                name
                id
            }
        }"""
        
        data = {
            "operationName":"FindManyUnit",
            "query": query,
            "variables": {"where": self._where}
        }

        self.unit_list = {u['name']:u['id'] for u in self._server.session().post(self._server.endpoint["graphql"], json = data).json()['data']['findManyUnit']}

    def unit(self, id:int) -> Unit:
        return Unit(self, id)

    def units(self, selected_unit_list:Optional[List[int]]=None) -> UnitIterrator:
        """
        Gets units of the program.

        Parameters:
        - selected_unit_list (Optional[List[int]]): A list of unit names to filter, default is None.

        Returns:
        - UnitIterator: An iterator over the filtered units.
        """

        if selected_unit_list is not None:
            units_data_filtered = [u for u in self.unit_list if u in selected_unit_list]
        else:
            units_data_filtered = self.unit_list

        return UnitIterrator(self, units_data_filtered)

    def __str__(self):
        return self.name + "\n" + str(self.units)
    
class UnitIterrator():
    """
    Iterator for Units.

    Attributes:
    - program: The program instance.
    - units (List[Dict]): List of unit data.
    """

    def __init__(self, program:Program, units:List[dict]):
        self.program = program
        self.units = units

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.units):
            unit = Unit(self.program, self.units[self.index]["name"])
            self.index = self.index + 1
            return unit
        else:
            raise StopIteration

class Unit(Fulldata, Captures):
    """
    Represents a unit with associated data.

    Attributes:
    - name (str): The name of the unit.
    - program: The program instance.
    """

    def __init__(self, program:Program, id:int) -> None:
        # Unit information
        self.program = program

        #
        self._where = {"some": {"id": {"equals": int(id)}}}

        #ToDo test campain list ?

        # Inits
        Fulldata.__init__(self, self.program._server, where=self._where)
        Captures.__init__(self, self.program._server, where=self._where)

    def __str__(self):
        return self.id

class TestCampaign(Fulldata, Captures):
    """
    Represents a test campaign associated with a unit.

    Attributes:
    - id (str): The ID of the test campaign.
    - unit: The unit instance.
    """

    def __init__(self, unit:Unit, id:int) -> None:
        # Unit information
        self.id = id
        self.unit = unit

        #
        self._where = {
            "AND": [
                self.unit.program._where,
                {"id": {"equals": int(id)}}
            ]
        }

        # Inits
        Fulldata.__init__(self, self.unit.program._server, where=self._where)
        Captures.__init__(self, self.unit.program._server, where=self._where)

    def __str__(self):
        return self.id