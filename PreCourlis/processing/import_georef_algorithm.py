from qgis.core import (
    QgsFeatureSink,
    QgsField,
    QgsProcessingException,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from PreCourlis.lib.mascaret.mascaretgeo_file import MascaretGeoFile
from PreCourlis.processing.precourlis_algorithm import PreCourlisAlgorithm


class ImportGeorefAlgorithm(PreCourlisAlgorithm):
    """
    This algorithm construct a PreCourlis structured line layer from a .geo or
    .georef file.
    """

    INPUT = "INPUT"
    CRS = "CRS"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterFile(self.INPUT, self.tr("Input file")))
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS, self.tr("Coordinates projection system"), "EPSG:4326"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("GeorefMascaret"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        input_path = self.parameterAsString(parameters, self.INPUT, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)

        file = MascaretGeoFile(input_path)

        fields = PreCourlisFileLine.base_fields()
        for layer_name in file.layer_names:
            fields.append(QgsField(layer_name, QVariant.String, len=100000))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            crs,
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        count = sum([len(r.sections) for r in file.reaches.values()])
        total = 100.0 / count if count else 0

        current = 0
        for reach in file.reaches.values():
            for section in reach.sections.values():
                # Stop the algorithm if cancel button has been clicked
                if feedback.isCanceled():
                    break

                feature = PreCourlisFileLine.feature_from_section(section, fields)

                # Add a feature in the sink
                sink.addFeature(feature, QgsFeatureSink.FastInsert)

                # Update the progress bar
                feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def name(self):
        return "import_georef"

    def displayName(self):
        return self.tr("Import Georef")

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return "Import"

    def createInstance(self):
        return ImportGeorefAlgorithm()
