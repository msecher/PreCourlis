import os

from qgis.core import QgsVectorLayer

import processing

from .. import DATA_PATH, EXPECTED_PATH, TEMP_PATH
from . import TestCase, OVERWRITE_EXPECTED

AXIS_PATH = os.path.join(DATA_PATH, "cas1", "axeHydroBief1.shp")
TRACKS_PATH = os.path.join(DATA_PATH, "cas1", "tracesBief1.shp")
DEM_PATH = os.path.join(DATA_PATH, "cas1", "cas2Mnt.asc")


class TestPrepareTracksAlgorithm(TestCase):
    def test_algorithm(self):
        output_path = os.path.join(TEMP_PATH, "prepare_tracks.gml")
        expected_path = os.path.join(EXPECTED_PATH, "prepare_tracks.gml")

        if OVERWRITE_EXPECTED:
            output_path = expected_path

        outputs = processing.run(
            "precourlis:prepare_tracks",
            {
                "TRACKS": TRACKS_PATH,
                "AXIS": AXIS_PATH,
                "FIRST_POS": 0.0,
                "NAME_FIELD": "nom_profil",
                "OUTPUT": output_path,
            },
        )
        output = QgsVectorLayer(outputs["OUTPUT"], "output", "ogr")
        assert output.isValid()

        expected = QgsVectorLayer(expected_path, "expected", "ogr")
        assert expected.isValid()
        self.assertLayersEqual(output, expected)