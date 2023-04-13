import os

from .. import DATA_PATH
from . import TestCase

AXIS_PATH = os.path.join(DATA_PATH, "input", "axeHydroBief1.shp")
TRACKS_PATH = os.path.join(DATA_PATH, "input", "tracesBief1.shp")
DEM_PATH = os.path.join(DATA_PATH, "input", "cas2Mnt.asc")


class TestPrepareTracksAlgorithm(TestCase):
    ALGORITHM_ID = "precourlis:prepare_tracks"
    DEFAULT_PARAMS = {
        "TRACKS": TRACKS_PATH,
        "AXIS": AXIS_PATH,
        "FIRST_POS": 0.0,
        "NAME_FIELD": "nom_profil",
    }

    def test_algorithm(self):
        self.check_algorithm({}, {"OUTPUT": "prepare_tracks.gml"})
