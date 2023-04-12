import os

from .. import EXPECTED_PATH, INPUT_PATH
from . import TestCase


class TestImportGeorefAlgorithm(TestCase):

    ALGORITHM_ID = "precourlis:import_georef"
    DEFAULT_PARAMS = {"CRS": "EPSG:2154"}

    def test_import_georef(self):
        self.check_algorithm(
            {os.path.join(INPUT_PATH, "test.georef")},
            {"OUTPUT": "import_georef.gml"},
        )

    def test_import_georefc(self):
        self.check_algorithm(
            {"INPUT": os.path.join(EXPECTED_PATH, "export_georef.georefC")},
            {"OUTPUT": "import_georefc.gml"},
        )
