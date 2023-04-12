from qgis.core import (
    QgsProcessing,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsGeometry,
    QgsLineString,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsFeatureRequest,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from PreCourlis.processing.precourlis_algorithm import PreCourlisAlgorithm


class PointsToLinesAlgorithm(PreCourlisAlgorithm):
    INPUT = "INPUT"
    AXIS = "AXIS"
    FIRST_SECTION_ABS_LONG = "FIRST_SECTION_ABS_LONG"
    FIRST_AXIS_POINT_ABS_LONG = "FIRST_AXIS_POINT_ABS_LONG"
    GROUP_FIELD = "GROUP_FIELD"
    ORDER_FIELD = "ORDER_FIELD"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input"),
                [QgsProcessing.TypeVectorPoint],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.AXIS,
                self.tr(
                    "Axis (needed to calculate axis_x and axis_y if not already set in source)"
                ),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.FIRST_SECTION_ABS_LONG,
                self.tr("Abscissa of first section"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.FIRST_AXIS_POINT_ABS_LONG,
                self.tr(
                    "Abscissa of axis first point"
                    " (take precedence over abscissa of first section when set)"
                ),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.GROUP_FIELD,
                self.tr("Group by field"),
                optional=True,
                parentLayerParameterName=self.INPUT,
                allowMultiple=False,
                defaultValue="sec_id",
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ORDER_FIELD,
                self.tr("Order by field"),
                optional=True,
                parentLayerParameterName=self.INPUT,
                allowMultiple=False,
                defaultValue="p_id",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Lines")),
            True,
        )

    def to_float(self, value):
        if value is None:
            return QVariant()
        return value

    def line_feature_from_points(self, point_features, sec_id, abs_long):
        points = [
            point_feature.geometry().constGet().clone()
            for point_feature in point_features
        ]
        line = QgsGeometry(QgsLineString(points))

        intersection_point = None
        if self.axis:
            intersection = line.intersection(self.axis.geometry())
            # Take only the first parts (QgsMultiPoint => QgsPoint)
            intersection_point = next(intersection.constParts()).clone()

        layers = PreCourlisFileLine(None).layers(point_features[0])

        line_feature = QgsFeature()
        line_feature.setAttributes(
            [
                # sec_id
                point_features[0].attribute("sec_id") or sec_id,
                # sec_name
                point_features[0].attribute("sec_name")
                or "{}_{:04.3f}".format("P" if abs_long >= 0 else "N", abs_long),
                # abs_long
                abs_long,
                # axis_x
                intersection_point.x()
                if self.axis
                else point_features[0].attribute("axis_x"),
                # axis_y
                intersection_point.y()
                if self.axis
                else point_features[0].attribute("axis_y"),
                # layers
                point_features[0].attribute("layers") or "",
                # p_id
                ",".join([str(id_ + 1) for id_ in range(0, len(points))]),
                # topo_bat
                ",".join([f.attribute("topo_bat") for f in point_features]),
                # abs_lat
                ",".join(
                    [str(line.lineLocatePoint(f.geometry())) for f in point_features]
                ),
                # zfond
                ",".join(
                    [str(self.to_float(f.attribute("zfond"))) for f in point_features]
                ),
            ]
            + [
                ",".join(
                    [str(self.to_float(f.attribute(layer))) for f in point_features]
                )
                for layer in layers
            ]
        )
        line_feature.setGeometry(line)
        return line_feature

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        axis = self.parameterAsSource(parameters, self.AXIS, context)
        self.first_section_abs_long = self.parameterAsDouble(
            parameters, self.FIRST_SECTION_ABS_LONG, context
        )
        if parameters.get(self.FIRST_AXIS_POINT_ABS_LONG, None) is None:
            self.first_axis_point_abs_long = None
        else:
            self.first_axis_point_abs_long = self.parameterAsDouble(
                parameters, self.FIRST_AXIS_POINT_ABS_LONG, context
            )
        group_field = self.parameterAsString(parameters, self.GROUP_FIELD, context)
        order_field = self.parameterAsString(parameters, self.ORDER_FIELD, context)

        self.axis = next(axis.getFeatures()) if axis else None

        request = QgsFeatureRequest()
        request.addOrderBy('"{}"'.format(group_field), True, True)

        file = PreCourlisFileLine(source)
        fields = PreCourlisFileLine.base_fields()
        for layer in file.layers():
            fields.append(QgsField(layer, QVariant.String, len=100000))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            source.sourceCrs(),
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures(request)

        group = None
        point_features = []
        sec_id = 0
        abs_long_offset = 0
        for current, point_feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            if current == 0:
                if self.first_axis_point_abs_long is not None:
                    abs_long_offset = self.first_axis_point_abs_long
                else:
                    abs_long_offset = (
                        self.first_section_abs_long
                        - point_feature.attribute("abs_long")
                    )

            if group is not None and point_feature.attribute(group_field) != group:
                sec_id += 1
                sink.addFeature(
                    self.line_feature_from_points(
                        sorted(point_features, key=lambda f: f.attribute(order_field)),
                        sec_id,
                        point_features[0].attribute("abs_long") + abs_long_offset,
                    ),
                    QgsFeatureSink.FastInsert,
                )
                group = None
                point_features = []

            group = point_feature.attribute(group_field)
            point_features.append(point_feature)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        if group is not None:
            sec_id += 1
            sink.addFeature(
                self.line_feature_from_points(
                    sorted(point_features, key=lambda f: f.attribute(order_field)),
                    sec_id,
                    point_features[0].attribute("abs_long") + abs_long_offset,
                ),
                QgsFeatureSink.FastInsert,
            )
            group = None

        return {self.OUTPUT: dest_id}

    def name(self):
        return "points_to_lines"

    def displayName(self):
        return self.tr("Points to lines")

    def group(self):
        return self.tr("Convert")

    def groupId(self):
        return "Convert"

    def createInstance(self):
        return PointsToLinesAlgorithm()
