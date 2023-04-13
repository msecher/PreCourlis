import os

from qgis.core import (
    QgsProcessingUtils,
    QgsVectorLayer,
)

from .. import DATA_PATH, EXPECTED_PATH, OVERWRITE_EXPECTED, TEMP_PATH
from ..utils import save_as_gml
from . import TestCase

SECTIONS_PATH = os.path.join(DATA_PATH, "input", "profiles_points.gml")
AXIS_PATH = os.path.join(DATA_PATH, "input", "axeHydroBief1.shp")
CONSTRAINT_LINES = [
    os.path.join(DATA_PATH, "input", "riveDroiteBief1.shp"),
    os.path.join(DATA_PATH, "input", "riveGaucheBief1.shp"),
]


class TestInterpolatePointsAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:interpolate_points"
    DEFAULT_PARAMS = {
        "SECTIONS": SECTIONS_PATH,
        "AXIS": AXIS_PATH,
        "CONSTRAINT_LINES": CONSTRAINT_LINES,
        "LONG_STEP": 200,
        "LAT_STEP": 50,
        "ATTR_CROSS_SECTION": "sec_id",
        "OUTPUT": QgsProcessingUtils.generateTempFilename("interpolate_points.shp"),
    }

    def test_algorithm(self):
        tmp_output = QgsProcessingUtils.generateTempFilename("interpolate_points.shp")
        self.check_algorithm(
            {"OUTPUT": tmp_output},
        )

        # Copy temporary layer to output
        expected = os.path.join(EXPECTED_PATH, "interpolate_points.gml")
        if OVERWRITE_EXPECTED:
            output = expected
        else:
            output = os.path.join(TEMP_PATH, "interpolate_points.gml")
        save_as_gml(QgsVectorLayer(tmp_output, "output", "ogr"), output)

        self.compare_layers(output, expected)
