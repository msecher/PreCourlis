from qgis.core import QgsProcessingException

from .. import PROFILE_LINES_PATH
from . import TestCase


class TestExportGeorefAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:export_mascaret"
    DEFAULT_PARAMS = {"INPUT": PROFILE_LINES_PATH}

    def compare_output(self, key, output, expected):
        self.compare_files(output, expected)

    def test_export_georef(self):
        self.check_algorithm({}, {"OUTPUT": "export_georef.georef"})

    def test_export_geo(self):
        self.check_algorithm({}, {"OUTPUT": "export_georef.geo"})

    def test_reach_name_validation(self):
        with self.assertRaises(
            QgsProcessingException, msg="Reach name cannot contain spaces"
        ):
            self.check_algorithm(
                {"REACH_NAME": "A name with spaces", "OUTPUT": "export_georef.georef"},
            )
