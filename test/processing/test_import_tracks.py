import os

from .. import DATA_PATH
from . import TestCase

AXIS_PATH = os.path.join(DATA_PATH, "input", "axeHydroBief1.shp")
TRACKS_PATH = os.path.join(DATA_PATH, "input", "tracesBief1.shp")
DEM_PATH = os.path.join(DATA_PATH, "input", "cas2Mnt.asc")


class TestImportTracksAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:import_tracks"
    DEFAULT_PARAMS = {
        "TRACKS": TRACKS_PATH,
        "AXIS": AXIS_PATH,
        "FIRST_SECTION_ABS_LONG": 0.0,
        "NAME_FIELD": "nom_profil",
        "DISTANCE": 100.0,
        "DEM": DEM_PATH,
    }

    def test_algorithm(self):
        self.check_algorithm({}, {"OUTPUT": "import_tracks.gml"})

    def test_no_strict_distance(self):
        self.check_algorithm(
            {"STRICT_DISTANCE": False},
            {"OUTPUT": "import_tracks_no_strict_distance.gml"},
        )

    def test_first_axis_point_abs_long(self):
        self.check_algorithm(
            {"FIRST_AXIS_POINT_ABS_LONG": 0.0},
            {"OUTPUT": "import_tracks_first_axis_point_abs_long.gml"},
        )
