from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsLineString,
    QgsPoint,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

from PreCourlis.core import is_null, to_float
from PreCourlis.core.utils import color_to_hex
from PreCourlis.lib.mascaret.mascaret_file import Reach, Section

DEFAULT_LAYER_COLOR = QColor("#7f7f7f")


class PreCourlisFileBase:
    def __init__(self, layer: QgsVectorLayer):
        self._layer = layer  # Layer is supposed to be the unique storage

    @staticmethod
    def section_fields():
        fields = QgsFields()
        # Section fields
        fields.append(QgsField("sec_id", QVariant.Int))
        fields.append(QgsField("sec_name", QVariant.String, len=80))
        fields.append(QgsField("abs_long", QVariant.Double))
        fields.append(QgsField("axis_x", QVariant.Double))
        fields.append(QgsField("axis_y", QVariant.Double))
        fields.append(QgsField("layers", QVariant.String, len=254))
        return fields

    def layer(self):
        return self._layer


class PreCourlisFileLine(PreCourlisFileBase):
    @staticmethod
    def base_fields():
        fields = PreCourlisFileBase.section_fields()
        # Point fields
        fields.append(QgsField("p_id", QVariant.String, len=100000))
        fields.append(QgsField("topo_bat", QVariant.String, len=100000))
        fields.append(QgsField("abs_lat", QVariant.String, len=100000))
        fields.append(QgsField("zfond", QVariant.String, len=100000))
        return fields

    def get_sections(self):
        for f in self._layer.getFeatures():
            yield self.section_from_feature(f)

    def section_from_feature(self, f):
        section = Section(
            my_id=f.attribute("sec_id"),
            name=f.attribute("sec_name"),
            pk=f.attribute("abs_long"),
        )
        section.axis = [f.attribute("axis_x"), f.attribute("axis_y")]

        def split_attribute(v, length):
            if is_null(v):
                return [None] * length
            return v.split(",")

        # Take only the first parts (QgsMultiLineString => QgsLineString)
        line = next(f.geometry().constParts()).clone()
        points = line.points()

        import numpy as np
        section.nb_points = len(points)
        section.x = np.array([p.x() for p in points])
        section.y = np.array([p.y() for p in points])
        section.z = np.array(
            [
                np.nan if is_null(z) else to_float(z)
                for z in split_attribute(f.attribute("zfond"), len(points))
            ]
        )
        section.distances = np.array(
            [
                to_float(d)
                for d in split_attribute(f.attribute("abs_lat"), len(points))
            ]
        )
        section.topo_bath = split_attribute(f.attribute("topo_bat"), len(points))

        layer_names = self.layers()
        layers_elev = [
            split_attribute(f.attribute(layer), len(points))
            for layer in self.layers()
        ]
        section.nlayers = len(layer_names)
        section.layer_names = layer_names
        section.layers_elev = np.array(
            [
                np.array([np.nan if is_null(v) else to_float(v) for v in values])
                for values in layers_elev
            ]
        )

        return section

    @classmethod
    def feature_from_section(cls, section, fields):
        feature = QgsFeature()
        feature.setFields(fields)
        for index, value in cls.attributes_from_section(section, fields).items():
            feature.setAttribute(index, value)
        feature.setGeometry(cls.geometry_from_section(section))
        return feature

    @staticmethod
    def geometry_from_section(section):
        return QgsGeometry(
            QgsLineString(
                [
                    QgsPoint(
                        x,
                        y,
                    )
                    if str(z) == "NULL"
                    else QgsPoint(x, y, z)
                    for x, y, z in zip(section.x, section.y, section.z)
                ]
            )
        )

    @staticmethod
    def attributes_from_section(section, fields):
        attributes = {
            "sec_id": section.id,
            "sec_name": section.name,
            "abs_long": section.pk,
            "axis_x": section.axis[0],
            "axis_y": section.axis[1],
            "layers": ",".join(section.layer_names),
            "p_id": ",".join([str(i) for i in range(0, len(section.distances))]),
            "topo_bat": ",".join(section.topo_bath),
            "abs_lat": ",".join([str(d) for d in section.distances]),
            "zfond": ",".join([str(z) for z in section.z]),
        }
        for i, layer in enumerate(section.layer_names):
            attributes[layer] = ",".join([str(z) for z in section.layers_elev[i]])
        return {
            fields.indexFromName(name): value
            for name, value in attributes.items()
        }

    def update_feature(self, fid, section, title):
        self._layer.beginEditCommand(title)
        self._layer.changeAttributeValues(
            fid, self.attributes_from_section(section, self._layer.fields())
        )
        self._layer.changeGeometry(fid, self.geometry_from_section(section))
        self._layer.endEditCommand()

    def get_reach(self, name=None):
        reach = Reach(
            my_id=0,
            name=name or self._layer.name(),
        )
        for section in self.get_sections():
            reach.add_section(section)
        return reach

    def layers(self, feature=None):
        if feature is None:
            request = QgsFeatureRequest()
            request.setFlags(QgsFeatureRequest.NoGeometry)
            request.setSubsetOfAttributes(["layers"], self._layer.fields())
            request.setLimit(1)
            feature = next(self._layer.getFeatures(request))
        value = feature.attribute("layers")
        if is_null(value) or value == "":
            return []
        return value.split(",")

    def layer_color(self, layer):
        default_color = "#7f7f7f"
        if layer == "zfond":
            default_color = "#ff0000"
        if self._layer is None:
            return default_color
        return self._layer.customProperty(
            "PreCoulis_{}_Color".format(layer), default_color
        )

    def set_layer_color(self, layer, color):
        key = "PreCoulis_{}_Color".format(layer)
        if color is None:
            self._layer.removeCustomProperty(key)
        else:
            self._layer.setCustomProperty(key, color_to_hex(color))

    def add_sedimental_layer(self, name, from_layer, deltaz=0):
        """
        Add new sedimental layer:
            - new layer value = from_layer value + delta
            - new layer is inserted before or after from_layer depending on delta
        """
        layers = self.layers()
        if self._layer.fields().indexFromName(name) != -1:
            raise KeyError("Field {} already exists".format(name))
        for field in self._layer.fields():
            if field.name().lower() == name.lower():
                raise KeyError("Field {} already exists".format(field.name()))

        # Update layers list and set value of new attributes
        if from_layer == "zfond":
            from_layer_index = -1
            if deltaz > 0:
                raise ValueError("Impossible to add layer on top of zfond")
        else:
            from_layer_index = layers.index(from_layer)
        new_layer_index = from_layer_index if deltaz > 0 else from_layer_index + 1
        layers.insert(new_layer_index, name)
        layers_list = ",".join(layers)

        self.layer().startEditing()
        self._layer.beginEditCommand("Add sedimental layer {}".format(name))

        # Add new attribute
        self._layer.addAttribute(QgsField(name, QVariant.String))
        self._layer.updateFields()

        layers_field_index = self._layer.fields().indexFromName("layers")
        source_field_index = self._layer.fields().indexFromName(from_layer)
        dest_field_index = self._layer.fields().indexFromName(name)

        for f in self._layer.getFeatures():
            self._layer.changeAttributeValue(f.id(), layers_field_index, layers_list)
            value = f.attribute(source_field_index)
            if not is_null(value):
                values = value.split(",")
                value = ",".join(
                    [str(v if v == "NULL" else float(v) + deltaz) for v in values]
                )
            self._layer.changeAttributeValue(f.id(), dest_field_index, value)

        self._layer.endEditCommand()

    def delete_sedimental_layer(self, name):
        self._layer.beginEditCommand("Remove sedimental layer {}".format(name))

        # Remove attribute
        field_index = self._layer.fields().indexFromName(name)
        self._layer.deleteAttribute(field_index)

        # Update layers list
        layers = self.layers()
        layers.pop(layers.index(name))
        layers_list = ",".join(layers)
        layers_field_index = self._layer.fields().indexFromName("layers")
        for f in self._layer.getFeatures():
            self._layer.changeAttributeValue(f.id(), layers_field_index, layers_list)

        self._layer.endEditCommand()

    def move_layer_up(self, name):
        if name == "zfond":
            raise ValueError("Impossible to move layer zfond")

        layers = self.layers()
        index = layers.index(name)

        if index == 0:
            raise ValueError("Impossible to move layer on top of zfond")

        self.layer().startEditing()
        self._layer.beginEditCommand("Move sedimental layer {}".format(name))

        layers.pop(layers.index(name))
        layers.insert(index - 1, name)

        layers_list = ",".join(layers)
        layers_field_index = self._layer.fields().indexFromName("layers")
        for f in self._layer.getFeatures():
            self._layer.changeAttributeValue(f.id(), layers_field_index, layers_list)

        self._layer.endEditCommand()

    def move_layer_down(self, name):
        if name == "zfond":
            raise ValueError("Impossible to move layer zfond")

        layers = self.layers()
        index = layers.index(name)

        if index == len(layers) - 1:
            raise ValueError("Impossible to move last layer down")

        self.layer().startEditing()
        self._layer.beginEditCommand("Move sedimental layer {}".format(name))

        layers.pop(layers.index(name))
        layers.insert(index + 1, name)

        layers_list = ",".join(layers)
        layers_field_index = self._layer.fields().indexFromName("layers")
        for f in self._layer.getFeatures():
            self._layer.changeAttributeValue(f.id(), layers_field_index, layers_list)

        self._layer.endEditCommand()


class PreCourlisFilePoint(PreCourlisFileBase):
    @staticmethod
    def base_fields():
        fields = PreCourlisFileBase.section_fields()
        # Point fields
        fields.append(QgsField("p_id", QVariant.Int))
        fields.append(QgsField("topo_bat", QVariant.String, len=1))
        fields.append(QgsField("abs_lat", QVariant.Double))
        fields.append(QgsField("x", QVariant.Double))
        fields.append(QgsField("y", QVariant.Double))
        fields.append(QgsField("zfond", QVariant.Double))
        return fields
