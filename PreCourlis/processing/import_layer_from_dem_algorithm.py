import math

from qgis.core import (
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingParameterBand,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
)

from PreCourlis.processing.precourlis_algorithm import PreCourlisAlgorithm


class ImportLayerFromDemAlgorithm(PreCourlisAlgorithm):
    INPUT = "INPUT"
    LAYER_NAME = "LAYER_NAME"
    DEM = "DEM"
    BAND = "BAND"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
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

    def sample_raster(self, raster, point, band):
        value, ok = raster.dataProvider().sample(point, band)

        if math.isnan(value):
            # Try average value from neighboring pixels
            pixel_x = raster.rasterUnitsPerPixelX()
            pixel_y = raster.rasterUnitsPerPixelY()
            values = []
            for dx in (-pixel_x, 0, +pixel_x):
                for dy in (-pixel_y, 0, +pixel_y):
                    neighbourg = QgsPointXY(point.x() + dx, point.y() + dy)
                    value, ok = raster.dataProvider().sample(neighbourg, band)
                    if not math.isnan(value):
                        values.append(value)
            if len(values) > 0:
                value = math.fsum(values) / len(values)

        if math.isnan(value):
            value = "NULL"

        return value

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        layer_name = self.parameterAsString(parameters, self.LAYER_NAME, context)
        raster = self.parameterAsRasterLayer(parameters, self.DEM, context)
        band = self.parameterAsInt(parameters, self.BAND, context)

        dest_field_index = layer.fields().indexFromName(layer_name)

        tr_context = QgsCoordinateTransformContext()
        transform = QgsCoordinateTransform(layer.crs(), raster.crs(), tr_context)

        # This algorithm directly edit input layer in place using edit buffer
        layer.startEditing()
        layer.beginEditCommand("Set values from DEM")

        total = 100.0 / layer.featureCount() if layer.featureCount() else 0
        for current, f in enumerate(layer.getFeatures()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            line = next(f.geometry().constParts()).clone()
            values = []
            for point in line.points():
                tr_point = transform.transform(QgsPointXY(point))
                values.append(self.sample_raster(raster, tr_point, band))
            value = ",".join([str(v) for v in values])
            layer.changeAttributeValue(f.id(), dest_field_index, value)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        layer.endEditCommand()

        return {}

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
