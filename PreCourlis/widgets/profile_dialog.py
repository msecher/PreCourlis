from pkg_resources import resource_filename

from qgis.core import (
    QgsFeatureRequest,
    QgsMapLayer,
    QgsProject,
    QgsWkbTypes,
)
from qgis.PyQt import QtCore, QtGui, QtWidgets, uic
from qgis.utils import iface

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from PreCourlis.widgets.delegates import FloatDelegate
from PreCourlis.widgets.points_table_model import PointsTableModel
from PreCourlis.widgets.sedimental_layer_model import SedimentalLayerModel

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(
    resource_filename("PreCourlis", "ui/profile_dialog_base.ui")
)


class SectionItem(QtGui.QStandardItem):
    def __init__(self, text, current_f_id, previous_f_id):
        super().__init__(text)
        self.current_f_id = current_f_id
        self.previous_f_id = previous_f_id
        self.next_f_id = None

    def set_next_f_id(self, next_f_id):
        self.next_f_id = next_f_id


class SectionItemModel(QtGui.QStandardItemModel):
    def setLayer(self, layer):
        self.beginResetModel()

        self.clear()
        if layer is None:
            return

        sec_name_index = layer.fields().indexFromName("sec_name")
        request = QgsFeatureRequest()
        request.addOrderBy("sec_id")
        request.setSubsetOfAttributes([sec_name_index])

        previous_f_id = None
        previous_item = None

        for f in layer.getFeatures(request):
            item = SectionItem(
                f.attribute(sec_name_index),
                f.id(),
                previous_f_id,
            )
            if previous_item is not None:
                previous_item.set_next_f_id(f.id())
            self.appendRow(item)

            previous_f_id = f.id()
            previous_item = item

        self.endResetModel()


class ProfileDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent, QtCore.Qt.Window)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.file = None
        self.editing = False
        self.interpolation = False
        self.current_section = None
        self.selected_color = None
        self.splitter.setSizes([200, 400])

        self.nav_toolbar = NavigationToolbar(self.graphWidget, self)
        self.sectionSelectionLayout.insertWidget(4, self.nav_toolbar)

        self.sectionItemModel = SectionItemModel(self)
        self.pointsTableModel = PointsTableModel(self)
        self.pointsTableModel.dataChanged.connect(self.data_changed)
        self.sedimentalLayerModel = SedimentalLayerModel(self)

        self.init_layer_combo_box()
        self.init_sections_combo_box()
        self.init_points_table_view()
        self.init_graph_widget()
        self.init_edition_panel()

        self.layer_changed(self.layer())

    def init_layer_combo_box(self):
        def accept_layer(layer):
            if layer.type() != QgsMapLayer.VectorLayer:
                return False
            if layer.geometryType() != QgsWkbTypes.LineGeometry:
                return False
            if layer.fields().indexFromName("sec_id") == -1:
                return False
            return True

        excluded_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if not accept_layer(layer):
                excluded_layers.append(layer)
        self.layerComboBox.setExceptedLayerList(excluded_layers)

        # Select active layer
        layer = iface.activeLayer()
        if layer not in excluded_layers:
            self.layerComboBox.setLayer(layer)

        self.layerComboBox.layerChanged.connect(self.layer_changed)

    def init_sections_combo_box(self):
        self.sectionComboBox.setModel(self.sectionItemModel)
        self.sectionComboBox.currentIndexChanged.connect(self.section_changed)
        self.previousSectionButton.clicked.connect(self.previous_section)
        self.nextSectionButton.clicked.connect(self.next_section)

    def init_points_table_view(self):
        self.pointsTableView.setItemDelegate(FloatDelegate(self))
        self.pointsTableView.setModel(self.pointsTableModel)

    def init_graph_widget(self):
        self.graphWidget.set_selection_model(self.pointsTableView.selectionModel())
        self.graphWidget.editing_finished.connect(self.graph_editing_finished)

    def init_edition_panel(self):
        self.sedimentalLayerComboBox.setModel(self.sedimentalLayerModel)
        self.sedimentalLayerComboBox.currentIndexChanged.connect(
            self.sedimental_layer_changed
        )
        self.addLayerColorButton.clicked.connect(self.add_layer_select_color)
        self.addLayerButton.clicked.connect(self.add_layer)
        self.applyLayerButton.clicked.connect(self.apply_layer)
        self.deleteLayerButton.clicked.connect(self.delete_layer)

        self.applyInterpolationButton.clicked.connect(self.apply_interpolation)

    def layer(self):
        return self.layerComboBox.currentLayer()

    def layer_changed(self, layer):
        if self.file is not None and self.file.layer() is not None:
            self.file.layer().layerModified.disconnect(self.layer_modified)

        self.file = PreCourlisFileLine(layer)
        self.sectionItemModel.setLayer(layer)
        self.sectionComboBox.setCurrentIndex(0)
        self.sedimentalLayerModel.setLayer(layer)
        self.sedimentalLayerComboBox.setCurrentIndex(0)

        if layer is not None:
            layer.layerModified.connect(self.layer_modified)

    def layer_modified(self):
        if not self.editing:
            self.section_changed(self.sectionComboBox.currentIndex())

    def section_from_feature_id(self, f_id):
        if f_id is None:
            return None
        f = self.layer().getFeature(f_id)
        section = self.file.section_from_feature(f)
        section.feature = f
        return section

    def section_changed(self, index):
        self.set_section(index)

    def set_section(self, index):
        if index == -1:
            self.graphWidget.clear()
            return

        item = self.sectionItemModel.item(index)

        # Select current feature in vector layer
        self.layer().selectByIds([item.current_f_id])

        self.current_section = self.section_from_feature_id(item.current_f_id)

        self.pointsTableModel.set_section(self.current_section)

        self.graphWidget.set_sections(
            self.layer(),
            self.layer().getFeature(item.current_f_id),
            self.section_from_feature_id(item.previous_f_id),
            self.current_section,
            self.section_from_feature_id(item.next_f_id),
        )

        # Reset navigation history
        self.nav_toolbar.update()
        if self.nav_toolbar._nav_stack() is None:
            self.nav_toolbar.push_current()  # set the home button to this view

    def previous_section(self):
        if self.sectionComboBox.currentIndex() < 1:
            return
        self.sectionComboBox.setCurrentIndex(self.sectionComboBox.currentIndex() - 1)

    def next_section(self):
        if self.sectionComboBox.currentIndex() > self.sectionItemModel.rowCount() - 2:
            return
        self.sectionComboBox.setCurrentIndex(self.sectionComboBox.currentIndex() + 1)

    def data_changed(self, topLeft, bottomRight, roles):
        if self.graphWidget.selection_tool.editing:
            return
        elif self.interpolation:
            return
        else:
            self.update_feature("Profile dialog table edit")

    def graph_editing_finished(self):
        self.update_feature("Profile dialog graph translation")

    def update_feature(self, title):
        self.layer().startEditing()
        self.editing = True
        self.file.update_feature(
            self.current_section.feature.id(),
            self.current_section,
            title,
        )
        self.editing = False
        self.graphWidget.refresh_current_section()

    def sedimental_layer(self):
        return self.sedimentalLayerComboBox.currentText()

    def sedimental_layer_changed(self, index):
        layer = self.sedimental_layer()
        self.addLayerNameLineEdit.setText(layer)
        self.set_new_layer_color(self.file.layer_color(layer))
        self.graphWidget.set_current_layer(layer)

    def add_layer_select_color(self):
        self.set_new_layer_color(
            QtWidgets.QColorDialog.getColor(
                self.selected_color or QtGui.QColor("#7f7f7f")
            )
        )

    def set_new_layer_color(self, color):
        stylesheet = ""
        if color is not None:
            if isinstance(color, str):
                color = QtGui.QColor(color)
            stylesheet = "background-color: rgba({}, {}, {}, 1);".format(
                color.red(),
                color.green(),
                color.blue(),
            )
        self.selected_color = color
        self.addLayerColorButton.setStyleSheet(stylesheet)

    def add_layer(self):
        name = self.addLayerNameLineEdit.text()

        self.layer().startEditing()
        self.file.add_sedimental_layer(
            name,
            self.sedimental_layer(),
            self.addLayerDeltaBox.value(),
        )
        self.file.set_layer_color(name, self.selected_color)

        self.sedimentalLayerModel.setLayer(self.layer())
        self.sedimentalLayerComboBox.setCurrentText(name)

        self.section_changed(self.sectionComboBox.currentIndex())

    def apply_layer(self):
        self.file.set_layer_color(self.sedimental_layer(), self.selected_color)
        self.graphWidget.refresh()

    def delete_layer(self):
        self.layer().startEditing()
        layer = self.sedimental_layer()
        self.sedimentalLayerComboBox.setCurrentIndex(
            self.sedimentalLayerComboBox.currentIndex() - 1
        )
        self.file.delete_sedimental_layer(layer)
        self.section_changed(self.sectionComboBox.currentIndex())

    def apply_interpolation(self):
        section = self.current_section

        dz0 = self.leftSpinBox.value()
        dz1 = self.leftSpinBox.value()

        index0 = None
        index1 = None
        model = self.pointsTableModel
        sel_model = self.pointsTableView.selectionModel()
        for index in sel_model.selection().indexes():
            if index0 is None:
                index0 = index.row()
            else:
                index0 = min(index0, index.row())

            if index1 is None:
                index1 = index.row()
            else:
                index1 = max(index1, index.row())

        x0 = section.distances[index0]
        x1 = section.distances[index1]

        columns = set([])
        for index in sel_model.selection().indexes():
            x = section.distances[index.row()]
            dz = dz0 + (x - x0) * (dz1 - dz0) / (x1 - x0)
            column = index.column()
            if column == 0:
                continue
            if column == 1:
                values = section.z
            else:
                values = section.layers_elev[column - 2]
            values[index.row()] += dz
            columns.add(column)

        self.interpolation = True
        self.pointsTableModel.dataChanged.emit(
            model.index(0, min(columns)),
            model.index(model.rowCount() - 1, max(columns)),
        )
        self.interpolation = False

        self.update_feature("Profile dialog interpolation")
