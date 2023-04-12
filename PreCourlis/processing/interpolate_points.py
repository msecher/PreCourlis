import os
import subprocess
from pkg_resources import resource_filename

from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsLineString,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorDestination,
    QgsProcessingUtils,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QVariant

import processing

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from PreCourlis.processing.precourlis_algorithm import PreCourlisAlgorithm

PYTHON_INTERPRETER = "python3"
ENCODING = "utf-8"

if os.name == "nt":
    PYTHON_INTERPRETER = "pythonw.exe"
    ENCODING = "cp1252"

PYTHON_SCRIPT = resource_filename(
    "PreCourlis", "lib/TatooineMesher/cli/densify_cross_sections.py"
)
PYTHONPATH = os.pathsep.join(
    [
        resource_filename("PreCourlis", "lib/TatooineMesher"),
        resource_filename(
            "PreCourlis",
            "lib/TatooineMesher/.venv/lib/python3.6/site-packages",
        ),
    ]
)


class ParameterShapefileDestination(QgsProcessingParameterVectorDestination):
    def supportedOutputVectorLayerExtensions(self):
        return ["shp"]

    def defaultFileExtension(self):
        return "shp"


class InterpolatePointsAlgorithm(PreCourlisAlgorithm):
    SECTIONS = "SECTIONS"
    AXIS = "AXIS"
    CONSTRAINT_LINES = "CONSTRAINT_LINES"
    LONG_STEP = "LONG_STEP"
    LAT_STEP = "LAT_STEP"
    ATTR_CROSS_SECTION = "ATTR_CROSS_SECTION"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SECTIONS,
                self.tr("Sections"),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.AXIS,
                self.tr("Axis"),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.CONSTRAINT_LINES,
                self.tr("Contraint lines"),
                layerType=QgsProcessing.TypeVectorLine,
                defaultValue=None,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LONG_STEP,
                self.tr("Longitudinal space step (in m)"),
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LAT_STEP,
                self.tr("Lateral space step (in m)"),
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTR_CROSS_SECTION,
                self.tr("Attribute to identify cross-sections"),
                parentLayerParameterName=self.SECTIONS,
                defaultValue=None,
            )
        )
        self.addParameter(
            ParameterShapefileDestination(self.OUTPUT, self.tr("Interpolated"))
        )

    def prepare_sections(self, parameters, context, feedback):
        sections = self.parameterAsSource(parameters, self.SECTIONS, context)

        # Prefix layer fields by "Z" for TatooineMesher
        file = PreCourlisFileLine(sections)
        alg_params = {
            "INPUT": parameters[self.SECTIONS],
            "FIELDS_MAPPING": [
                {"name": "sec_id", "type": QVariant.Int, "expression": '"sec_id"'},
                {"name": "p_id", "type": QVariant.Int, "expression": '"p_id"'},
                {"name": "Zzfond", "type": QVariant.Double, "expression": '"zfond"'},
            ]
            + [
                {
                    "name": "Z{}".format(layer),
                    "type": QVariant.Double,
                    "expression": '"{}"'.format(layer),
                }
                for layer in file.layers()
            ],
            "OUTPUT": QgsProcessingUtils.generateTempFilename("tatooine_input.shp"),
        }
        outputs = processing.run(
            "qgis:refactorfields",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        return outputs["OUTPUT"]

    def prepare_constraint_lines(self, parameters, context, feedback):
        sections = self.parameterAsSource(parameters, self.SECTIONS, context)

        # Merge constraint lines files
        outputs = processing.run(
            "native:mergevectorlayers",
            {
                "LAYERS": parameters[self.CONSTRAINT_LINES],
                "CRS": sections.sourceCrs(),
                "OUTPUT": QgsProcessingUtils.generateTempFilename(
                    "constraint_lines.shp"
                ),
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        constraint_lines = outputs["OUTPUT"]

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Add lines with first and last points of sections
        request = QgsFeatureRequest()
        request.addOrderBy('"sec_id"', True, True)
        request.addOrderBy('"p_id"', True, True)

        previous_sec_id = None
        previous_point = None
        left_line = QgsLineString()
        right_line = QgsLineString()
        total = total = (
            100.0 / sections.featureCount() if sections.featureCount() else 0
        )
        for current, f in enumerate(sections.getFeatures(request)):
            if previous_sec_id is None or previous_sec_id != f.attribute("sec_id"):
                if previous_sec_id is not None:
                    right_line.addVertex(previous_point)
                left_line.addVertex(f.geometry().constGet())
            previous_sec_id = f.attribute("sec_id")
            previous_point = f.geometry().constGet()

            feedback.setProgress(int(current * total))

        right_line.addVertex(previous_point)

        constraint_lines_layer = QgsVectorLayer(
            constraint_lines, "constraint_lines", "ogr"
        )
        dp = constraint_lines_layer.dataProvider()
        left = QgsFeature()
        left.setGeometry(QgsGeometry(left_line))
        right = QgsFeature()
        right.setGeometry(QgsGeometry(right_line))
        dp.addFeatures([left, right])

        return constraint_lines

    def processAlgorithm(self, parameters, context, model_feedback):
        constraint_lines = self.parameterAsLayerList(
            parameters,
            self.CONSTRAINT_LINES,
            context,
        )

        feedback = QgsProcessingMultiStepFeedback(
            4 if constraint_lines else 2, model_feedback
        )

        sections_prepared = self.prepare_sections(parameters, context, feedback)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        if constraint_lines:
            constraint_lines = self.prepare_constraint_lines(
                parameters, context, feedback
            )
            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}

        axis_path = self.parameterAsCompatibleSourceLayerPath(
            parameters,
            self.AXIS,
            context,
            compatibleFormats=["shp"],
        )
        long_step = self.parameterAsString(parameters, self.LONG_STEP, context)
        lat_step = self.parameterAsString(parameters, self.LAT_STEP, context)
        attr_cross_sections = self.parameterAsString(
            parameters, self.ATTR_CROSS_SECTION, context
        )
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        command = [
            PYTHON_INTERPRETER,
            PYTHON_SCRIPT,
            "-v",
        ]
        if constraint_lines:
            command += [
                "--infile_constraint_lines",
                constraint_lines,
            ]
        command += [
            "--long_step",
            long_step,
            "--lat_step",
            lat_step,
            "--attr_cross_sections",
            attr_cross_sections,
            axis_path,
            sections_prepared,
            output_path,
        ]

        feedback.pushCommandInfo(" ".join(command))

        env = {key: value for key, value in os.environ.items()}
        env["PYTHONPATH"] = os.pathsep.join([env.get("PYTHONPATH", ""), PYTHONPATH])

        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            env=env,
            encoding=ENCODING,
        ) as proc:
            while proc.poll() is None:
                for line in iter(proc.stdout.readline, ""):
                    feedback.pushConsoleInfo(line.strip())
            for line in iter(proc.stdout.readline, ""):
                feedback.pushConsoleInfo(line.strip())
            if proc.returncode != 0:
                raise QgsProcessingException(
                    "Failed to execute command {}".format(" ".join(command))
                )

        sections = self.parameterAsSource(parameters, self.SECTIONS, context)
        processing.run(
            "qgis:definecurrentprojection",
            {"INPUT": output_path, "CRS": sections.sourceCrs()},
        )

        return {self.OUTPUT: output_path}

    def name(self):
        return "interpolate_points"

    def displayName(self):
        return self.tr("Interpolate points")

    def group(self):
        return self.tr("Interpolate")

    def groupId(self):
        return "Interpolate"

    def createInstance(self):
        return InterpolatePointsAlgorithm()
