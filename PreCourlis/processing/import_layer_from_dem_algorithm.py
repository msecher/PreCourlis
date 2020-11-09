from qgis.core import (
    QgsProcessing,
    QgsProcessingMultiStepFeedback,
    QgsProcessingOutputLayerDefinition,
    QgsProcessingParameterBand,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
)
import processing

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from PreCourlis.processing.precourlis_algorithm import PreCourlisAlgorithm


class ImportLayerFromDemAlgorithm(PreCourlisAlgorithm):

    INPUT = "INPUT"
    LAYER_NAME = "LAYER_NAME"
    DEM = "DEM"
    BAND = "BAND"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input"),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.LAYER_NAME, self.tr("Layer name"), defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM, self.tr("Digital Elevation Model"), defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterBand(
                self.BAND,
                self.tr("Band number"),
                1,
                "RASTER",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Layer added"))
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        source = self.parameterAsSource(parameters, self.INPUT, context)

        # setzfromraster
        alg_params = {
            "INPUT": parameters[self.INPUT],
            "RASTER": parameters[self.DEM],
            "BAND": parameters[self.BAND],
            "NODATA": 999999,
            "SCALE": 1,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["SetZFromRaster"] = processing.run(
            "native:setzfromraster",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["SetZFromRaster"]["OUTPUT"]

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        layer_name = self.parameterAsString(parameters, self.LAYER_NAME, context)

        # temporary alter the output of setzfromraster
        layer = context.getMapLayer(current)
        assert layer.isValid()
        file = PreCourlisFileLine(layer)
        assert layer.startEditing()
        file.add_sedimental_layer(layer_name)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        output = QgsProcessingOutputLayerDefinition(parameters[self.OUTPUT])
        output.destinationName = self.tr("Layer added")

        # assignprojection (save layer to specified output)
        alg_params = {
            "INPUT": current,
            "CRS": source.sourceCrs(),
            "OUTPUT": output,
        }
        outputs["AssignProjection"] = processing.run(
            "native:assignprojection",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["AssignProjection"]["OUTPUT"]

        results["OUTPUT"] = current
        return results

    def name(self):
        return "import_layer_from_dem"

    def displayName(self):
        return self.tr("Import layer from DEM")

    def group(self):
        return self.tr("Import")

    def groupId(self):
        return "Import"

    def createInstance(self):
        return ImportLayerFromDemAlgorithm()
