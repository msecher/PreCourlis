import os

from .. import DATA_PATH, PROFILE_LINES_PATH
from . import TestCase

DEM_PATH = os.path.join(DATA_PATH, "input", "cas2Mnt.asc")


class TestImportTracksAlgorithm(TestCase):

    ALGORITHM_ID = "precourlis:import_layer_from_dem"
    DEFAULT_PARAMS = {
        "INPUT": PROFILE_LINES_PATH,
        "LAYER_NAME": "from_dem",
        "DEM": DEM_PATH,
        "BAND": 1,
    }

    def test_algorithm(self):
        self.check_algorithm({}, {"OUTPUT": "import_layer_from_dem.gml"})
