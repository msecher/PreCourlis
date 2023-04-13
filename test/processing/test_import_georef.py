import os

from .. import DATA_PATH
from . import TestCase

GEOREF_PATH = os.path.join(DATA_PATH, "input", "test.georef")


class TestImportGeorefAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:import_georef"
    DEFAULT_PARAMS = {"INPUT": GEOREF_PATH, "CRS": "EPSG:2154"}

    def test_algorithm(self):
        self.check_algorithm({}, {"OUTPUT": "import_georef.gml"})
