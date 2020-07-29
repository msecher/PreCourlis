from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingUtils,
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant
import processing


class InterpolateLinesAlgorithm(QgsProcessingAlgorithm):

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
                types=[QgsProcessing.TypeVectorLine],
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
                self.LAT_STEP, self.tr("Lateral space step (in m)"), defaultValue=None,
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
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Interpolated"))
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        sections = self.parameterAsSource(parameters, self.SECTIONS, context)

        # Lines to points
        alg_params = {
            "INPUT": parameters[self.SECTIONS],
            "OUTPUT": QgsProcessingUtils.generateTempFilename("lines_to_points.shp"),
        }
        outputs["LinesToPoints"] = processing.run(
            "precourlis:lines_to_points",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["LinesToPoints"]["OUTPUT"]

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Interpolate points
        alg_params = {
            "SECTIONS": current,
            "AXIS": parameters[self.AXIS],
            "CONSTRAINT_LINES": parameters[self.CONSTRAINT_LINES],
            "LONG_STEP": parameters[self.LONG_STEP],
            "LAT_STEP": parameters[self.LAT_STEP],
            "ATTR_CROSS_SECTION": "sec_id",
            "OUTPUT": QgsProcessingUtils.generateTempFilename("interpolate_points.shp"),
        }
        outputs["InterpolatePoints"] = processing.run(
            "precourlis:interpolate_points",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["InterpolatePoints"]["OUTPUT"]

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # assignprojection
        alg_params = {
            "INPUT": current,
            "CRS": sections.sourceCrs(),
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["AssignProjection"] = processing.run(
            "native:assignprojection",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["AssignProjection"]["OUTPUT"]

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        alg_params = {
            "INPUT": current,
            "FIELDS_MAPPING": [
                {"name": "sec_id", "type": QVariant.Int, "expression": ""},
                {"name": "sec_name", "type": QVariant.String, "expression": ""},
                {"name": "abs_long", "type": QVariant.Double, "expression": '"Xl"'},
                {"name": "axis_x", "type": QVariant.Double, "expression": ""},
                {"name": "axis_y", "type": QVariant.Double, "expression": ""},
                {"name": "p_id", "type": QVariant.Int, "expression": ""},
                {"name": "xt", "type": QVariant.Int, "expression": "xt"},
                {"name": "abs_lat", "type": QVariant.Double, "expression": ""},
                {"name": "zfond", "type": QVariant.Double, "expression": '"Z"'},
            ],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            # "OUTPUT": parameters[self.OUTPUT],
        }
        outputs["RefactorFields"] = processing.run(
            "qgis:refactorfields",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["RefactorFields"]["OUTPUT"]

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Points to lines
        alg_params = {
            "INPUT": current,
            "AXIS": parameters[self.AXIS],
            "GROUP_FIELD": "abs_long",
            "ORDER_FIELD": "xt",
            "OUTPUT": parameters[self.OUTPUT],
        }
        outputs["PointsToLines"] = processing.run(
            "precourlis:points_to_lines",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["PointsToLines"]["OUTPUT"]

        results["OUTPUT"] = current
        return results

    def name(self):
        return "interpolate_lines"

    def displayName(self):
        return self.tr("Interpolate lines")

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return "Interpolate"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return InterpolateLinesAlgorithm()
