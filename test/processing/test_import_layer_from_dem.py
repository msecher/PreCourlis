import os

from qgis.core import QgsVectorLayer

from .. import (
    DATA_PATH,
    EXPECTED_PATH,
    OVERWRITE_EXPECTED,
    PROFILE_LINES_PATH,
    TEMP_PATH,
)
from ..utils import save_as_gml
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
        layer = QgsVectorLayer(PROFILE_LINES_PATH)

        self.check_algorithm(
            {
                "INPUT": layer,
            }
        )

        # Copy temporary layer to output
        expected = os.path.join(EXPECTED_PATH, "import_layer_from_dem.gml")
        if OVERWRITE_EXPECTED:
            output = expected
        else:
            output = os.path.join(TEMP_PATH, "import_layer_from_dem.gml")
        save_as_gml(layer, output)

        self.compare_layers(output, expected)
