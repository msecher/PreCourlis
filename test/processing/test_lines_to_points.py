import os

from .. import DATA_PATH, PROFILE_LINES_PATH
from . import TestCase


class TestLinesToPointsAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:lines_to_points"
    DEFAULT_PARAMS = {
        "INPUT": PROFILE_LINES_PATH,
    }

    def test_line_to_points(self):
        self.check_algorithm({}, {"OUTPUT": "lines_to_points.gml"})

    def test_lines_to_points_with_zero_layers(self):
        self.check_algorithm(
            {
                "INPUT": os.path.join(
                    DATA_PATH, "input", "profiles_lines_zero_layers.geojson"
                )
            },
            {"OUTPUT": "lines_to_points_with_zero_layers.gml"},
        )
