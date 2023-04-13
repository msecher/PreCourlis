import os

from .. import DATA_PATH
from . import TestCase


class TestPointsToLinesAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:points_to_lines"
    DEFAULT_PARAMS = {
        "INPUT": os.path.join(DATA_PATH, "input", "profiles_points.gml"),
    }

    def test_algorithm(self):
        self.check_algorithm({}, {"OUTPUT": "points_to_lines.gml"})
