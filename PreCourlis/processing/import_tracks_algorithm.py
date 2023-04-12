from qgis.core import (
    QgsApplication,
    QgsProcessing,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterField,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorDestination,
)
import processing

from PreCourlis.processing.precourlis_algorithm import PreCourlisAlgorithm


class ImportTracksAlgorithm(PreCourlisAlgorithm):
    TRACKS = "TRACKS"
    AXIS = "AXIS"
    FIRST_SECTION_ABS_LONG = "FIRST_SECTION_ABS_LONG"
    FIRST_AXIS_POINT_ABS_LONG = "FIRST_AXIS_POINT_ABS_LONG"
    NAME_FIELD = "NAME_FIELD"
    DISTANCE = "DISTANCE"
    STRICT_DISTANCE = "STRICT_DISTANCE"
    DEM = "DEM"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TRACKS,
                self.tr("Tracks"),
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
                self.NAME_FIELD,
                self.tr("Name field"),
                optional=True,
                type=QgsProcessingParameterField.String,
                parentLayerParameterName=self.TRACKS,
                allowMultiple=False,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                self.tr("Maximum distance between two points"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.STRICT_DISTANCE,
                self.tr("Apply strict distance (do not keep initial points)"),
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM, self.tr("Digital Elevation Model"), defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr("Sections"),
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=None,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(8, model_feedback)
        results = {}
        outputs = {}

        tracks = self.parameterAsSource(parameters, self.TRACKS, context)

        # prepare_tracks
        alg_params = {
            "TRACKS": parameters[self.TRACKS],
            "AXIS": parameters[self.AXIS],
            "NAME_FIELD": parameters[self.NAME_FIELD],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["PrepareTracks"] = processing.run(
            "precourlis:prepare_tracks",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["PrepareTracks"]["OUTPUT"]

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # addautoincrementalfield
        alg_params = {
            "INPUT": current,
            "FIELD_NAME": "sec_index",
            "START": 1,
            "GROUP_FIELDS": [],
            "SORT_EXPRESSION": '"abs_long"',
            "SORT_ASCENDING": True,
            "SORT_NULLS_FIRST": False,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["AddAutoincrementalField"] = processing.run(
            "native:addautoincrementalfield",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["AddAutoincrementalField"]["OUTPUT"]

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # fieldcalculator
        alg_params = {
            "INPUT": current,
            "FIELD_NAME": "sec_id",
            "FIELD_TYPE": 0,
            "FIELD_LENGTH": 10,
            "FIELD_PRECISION": 3,
            "NEW_FIELD": False,
            "FORMULA": ' "sec_index" ',
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["FieldCalculator"] = processing.run(
            "qgis:fieldcalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["FieldCalculator"]["OUTPUT"]

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        strict_distance = self.parameterAsBool(
            parameters, self.STRICT_DISTANCE, context
        )
        if strict_distance:
            # pointsalonglines
            alg_params = {
                "INPUT": current,
                "DISTANCE": parameters[self.DISTANCE],
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }
            outputs["PointsAlongLines"] = processing.run(
                "precourlis:pointsalonglines",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )
            current = outputs["PointsAlongLines"]["OUTPUT"]
            points_order_field = "distance"
        else:
            # v.to.points
            v_to_points = QgsApplication.processingRegistry().createAlgorithmById(
                "grass7:v.to.points"
            )
            alg_params = {
                "-i": True,
                "-t": False,
                "dmax": parameters[self.DISTANCE],
                "input": current,
                "type": [1],
                "use": 1,
                "output": v_to_points.parameterDefinition(
                    "output"
                ).generateTemporaryDestination(),
            }
            outputs["Vtopoints"] = processing.run(
                "grass7:v.to.points",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )
            current = outputs["Vtopoints"]["output"]
            points_order_field = "fid"

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # assignprojection
        alg_params = {
            "INPUT": current,
            "CRS": tracks.sourceCrs(),
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

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # point_to_lines
        alg_params = {
            "INPUT": current,
            "FIRST_SECTION_ABS_LONG": parameters.get(self.FIRST_SECTION_ABS_LONG, None),
            "FIRST_AXIS_POINT_ABS_LONG": parameters.get(
                self.FIRST_AXIS_POINT_ABS_LONG, None
            ),
            "GROUP_FIELD": "sec_id",
            "ORDER_FIELD": points_order_field,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["PointsToLines"] = processing.run(
            "precourlis:points_to_lines",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["PointsToLines"]["OUTPUT"]

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # import_layer_from_dem (edit layer in place with edit buffer)
        layer = context.getMapLayer(current)
        alg_params = {
            "INPUT": layer,
            "LAYER_NAME": "zfond",
            "DEM": parameters[self.DEM],
            "BAND": 1,
        }
        outputs["ImportLayerFromDem"] = processing.run(
            "precourlis:import_layer_from_dem",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # orderbyexpression (dump layer with changes from edit buffer)
        layer.selectAll()
        alg_params = {
            "INPUT": layer,
            "EXPRESSION": '"sec_id"',
            "ASCENDING": True,
            "NULLS_FIRST": False,
            "OUTPUT": self.parameterAsOutputLayer(parameters, self.OUTPUT, context),
        }
        outputs["OrderByExpression"] = processing.run(
            "native:orderbyexpression",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        current = outputs["OrderByExpression"]["OUTPUT"]

        results["OUTPUT"] = current
        return results

    def name(self):
        return "import_tracks"

    def displayName(self):
        return self.tr("Import tracks")

    def group(self):
        return self.tr("Import")

    def groupId(self):
        return "Import"

    def createInstance(self):
        return ImportTracksAlgorithm()
