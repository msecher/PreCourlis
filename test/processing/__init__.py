import filecmp
import os
from unittest import TestCase as TestCaseBase

from qgis.analysis import QgsNativeAlgorithms
from qgis.core import QgsApplication
from qgis.core import QgsVectorLayer

import processing
from processing import Processing

from PreCourlis.processing.precourlis_provider import PreCourlisProvider

from .. import (
    EXPECTED_PATH,
    TEMP_PATH,
    OVERWRITE_EXPECTED,
)

QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
Processing.initialize()


class TestCase(TestCaseBase):
    ALGORITHM_ID = None
    DEFAULT_PARAMS = {}

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        cls.precourlis_provider = PreCourlisProvider()
        assert QgsApplication.processingRegistry().addProvider(cls.precourlis_provider)

    @classmethod
    def tearDownClass(cls):
        super(TestCase, cls).tearDownClass()
        QgsApplication.processingRegistry().removeProvider(cls.precourlis_provider)

    def check_algorithm(self, inputs={}, output_filenames={}):
        outputs = {}
        expected = {}
        for key, filename in output_filenames.items():
            expected[key] = os.path.join(EXPECTED_PATH, filename)

            if OVERWRITE_EXPECTED:
                outputs[key] = expected[key]
            else:
                outputs[key] = os.path.join(TEMP_PATH, filename)

        outputs = processing.run(
            self.ALGORITHM_ID,
            {
                **self.DEFAULT_PARAMS,
                **outputs,
                **inputs,
            },
        )

        for key in expected:
            self.compare_output(key, outputs[key], expected[key])

    def compare_output(self, key, output, expected):
        self.compare_layers(output, expected)

    def compare_layers(self, output, expected):
        output_layer = QgsVectorLayer(output, "output", "ogr")
        assert output_layer.isValid()

        expected_layer = QgsVectorLayer(expected, "expected", "ogr")
        assert expected_layer.isValid()

        self.assertLayersEqual(expected_layer, output_layer)

    def compare_files(self, output, expected):
        assert os.path.isfile(output)
        assert filecmp.cmp(expected, output)
