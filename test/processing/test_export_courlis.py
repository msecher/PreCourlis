from qgis.core import QgsProcessingException

from .. import PROFILE_LINES_PATH
from . import TestCase


class TestExportGeorefAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:export_courlis"
    DEFAULT_PARAMS = {"INPUT": PROFILE_LINES_PATH}

    def compare_output(self, key, output, expected):
        self.compare_files(output, expected)

    def test_export_georefc(self):
        self.check_algorithm({}, {"OUTPUT": "export_georef.georefC"})

    def test_export_geoc(self):
        self.check_algorithm({}, {"OUTPUT": "export_georef.geoC"})

    def test_reach_name_validation(self):
        with self.assertRaises(
            QgsProcessingException, msg="Reach name cannot contain spaces"
        ):
            self.check_algorithm(
                {"REACH_NAME": "A name with spaces", "OUTPUT": "test.georefC"},
            )
