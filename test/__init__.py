import os

# import qgis libs so that ve set the correct sip api version
import qgis  # pylint: disable=W0611  # NOQA

from qgis import utils as qgis_utils
from qgis.testing import start_app
from qgis.testing.mocked import get_iface

QGIS_APP = start_app()

iface = get_iface()
iface.activeLayer.return_value = None
qgis_utils.iface = iface

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
INPUT_PATH = os.path.join(DATA_PATH, "data", "input")
EXPECTED_PATH = os.path.join(DATA_PATH, "data", "expected")
OUTPUT_PATH = os.path.join(DATA_PATH, "data", "output")
TEMP_PATH = "/tmp"

PROFILE_LINES_PATH = os.path.join(DATA_PATH, "input", "profiles_lines.geojson")

OVERWRITE_EXPECTED = os.environ.get("OVERWRITE_EXPECTED", False)
