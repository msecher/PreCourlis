import os

from qgis.core import QgsVectorLayer

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from .. import (
    DATA_PATH,
    PROFILE_LINES_PATH,
)
from . import TestCase

AXIS_PATH = os.path.join(DATA_PATH, "input", "axeHydroBief1.shp")
CONSTRAINT_LINES = [
    os.path.join(DATA_PATH, "input", "riveDroiteBief1.shp"),
    os.path.join(DATA_PATH, "input", "riveGaucheBief1.shp"),
]


class TestInterpolateLinesAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:interpolate_lines"
    DEFAULT_PARAMS = {
        "SECTIONS": PROFILE_LINES_PATH,
        "AXIS": AXIS_PATH,
        "LONG_STEP": 200,
        "LAT_STEP": 20,
        "ATTR_CROSS_SECTION": "sec_id",
    }

    def test_interpolate_lines(self):
        self.check_algorithm(
            {},
            {"OUTPUT": "interpolate_lines.gml"},
        )

    def test_interpolate_lines_with_constraints(self):
        self.check_algorithm(
            {"CONSTRAINT_LINES": CONSTRAINT_LINES},
            {"OUTPUT": "interpolate_lines_with_constraints.gml"},
        )

    def test_interpolate_lines_multiple_layers(self):
        layer = QgsVectorLayer(PROFILE_LINES_PATH, "multiple_layers", "ogr")
        file = PreCourlisFileLine(layer)
        file.add_sedimental_layer("Layer2", "Layer1", -1.0)
        self.check_algorithm(
            {"SECTIONS": layer},
            {"OUTPUT": "interpolate_lines_multiple_layers.gml"},
        )
