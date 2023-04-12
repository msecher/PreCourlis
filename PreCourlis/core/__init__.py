from collections import OrderedDict
import numpy as np

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsLineString,
    QgsPoint,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QVariant

from PreCourlis.lib.mascaret.mascaret_file import (
    Section as SectionBase,
    Reach as ReachBase,
)

TEMP_FOLDER = "/tmp/PreCourlis"


def is_null(v):
    if v is None:
        return True
    if isinstance(v, QVariant) and v.isNull():
        return True
    if isinstance(v, str) and v == "NULL":
        return True
    return False


def to_float(v):
    if v is None:
        return None
    if isinstance(v, QVariant) and v.isNull():
        return None
    if v == "NULL":
        return None
    return float(v)
