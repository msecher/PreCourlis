from pkg_resources import resource_filename

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from qgis.core import (
    QgsApplication,
    QgsMapLayer,
    QgsMapLayerProxyModel,
    QgsProject,
    QgsWkbTypes,
)
from qgis.gui import QgsMessageBar
from qgis.PyQt import QtCore, QtGui, QtWidgets, uic
from qgis.utils import iface
import processing

from PreCourlis.core.precourlis_file import PreCourlisFileLine, DEFAULT_LAYER_COLOR
from PreCourlis.widgets.delegates import FloatDelegate
from PreCourlis.widgets.points_table_model import PointsTableModel
from PreCourlis.widgets.section_item_model import SectionItemModel
from PreCourlis.widgets.sedimental_layer_model import SedimentalLayerModel

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(
    resource_filename("PreCourlis", "ui/profile_dialog_base.ui")
)


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

        self.undoButton.setIcon(QgsApplication.getThemeIcon("/mActionUndo.svg"))
        self.undoButton.clicked.connect(self.undo)
        undo_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtGui.QKeySequence.Undo), self
        )
        undo_shortcut.activated.connect(self.undo)

        self.redoButton.setIcon(QgsApplication.getThemeIcon("/mActionRedo.svg"))
        self.redoButton.clicked.connect(self.redo)
        redo_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtGui.QKeySequence.Redo), self
        )
        redo_shortcut.activated.connect(self.redo)

        self.saveButton.setIcon(QgsApplication.getThemeIcon("/mActionSaveAllEdits.svg"))
        self.saveButton.clicked.connect(self.save)
        save_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtGui.QKeySequence.Save), self
        )
        save_shortcut.activated.connect(self.save)

        self.nav_toolbar = NavigationToolbar(self.graphWidget, self)
        self.sectionSelectionLayout.insertWidget(7, self.nav_toolbar)

        self.message_bar = QgsMessageBar(self)
        self.layout().insertWidget(1, self.message_bar)

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
        self.pointsTableView.setItemDelegateForColumn(
            self.pointsTableModel.columns.index("topo_bat"),
            QtWidgets.QStyledItemDelegate(self),
        )
        self.pointsTableView.setModel(self.pointsTableModel)

    def init_graph_widget(self):
        self.graphWidget.set_selection_model(self.pointsTableView.selectionModel())
        self.graphWidget.editing_finished.connect(self.graph_editing_finished)

    def init_edition_panel(self):
        self.sedimentalLayerComboBox.setModel(self.sedimentalLayerModel)
        self.sedimentalLayerComboBox.currentIndexChanged.connect(
            self.sedimental_layer_changed
        )
        self.addLayerColorButton.clicked.connect(self.addLayerColorButton_clicked)
        self.moveLayerUpButton.setIcon(
            QgsApplication.getThemeIcon("/mActionArrowUp.svg")
        )
        self.moveLayerUpButton.clicked.connect(self.move_layer_up)
        self.moveLayerDownButton.setIcon(
            QgsApplication.getThemeIcon("/mActionArrowDown.svg")
        )
        self.moveLayerDownButton.clicked.connect(self.move_layer_down)
        self.addLayerButton.clicked.connect(self.add_layer)
        self.applyLayerButton.clicked.connect(self.apply_layer)
        self.deleteLayerButton.clicked.connect(self.delete_layer)
        self.extractLayerZDEMComboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.extractLayerZButton.clicked.connect(self.extract_layer_z)

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
            self.sedimental_layers_update()
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
        model = self.pointsTableModel
        model.dataChanged.emit(
            model.index(0, 1),
            model.index(model.rowCount() - 1, model.columnCount() - 1),
        )
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

    def undo(self):
        self.layer().undoStack().undo()

    def redo(self):
        self.layer().undoStack().redo()

    def save(self):
        layer = self.layer()
        ok = layer.commitChanges()
        if not ok:
            self.message_bar.pushCritical(
                self.tr("Save Layer Edits"),
                self.tr("Could not commit changes to layer {}\n\nErrors: {}\n").format(
                    layer.name(), "\n".join(layer.commitErrors())
                ),
            )

    def sedimental_layers_update(self, name=None):
        if name is None:
            name = self.sedimental_layer()
        self.sedimentalLayerModel.setLayer(self.layer())
        self.sedimentalLayerComboBox.setCurrentText(name)

    def sedimental_layer(self):
        return self.sedimentalLayerComboBox.currentText()

    def sedimental_layer_changed(self, index):
        layer = self.sedimental_layer()
        self.addLayerNameLineEdit.setText(layer)
        self.set_layer_color_button_color(self.file.layer_color(layer))
        self.graphWidget.set_current_layer(layer)

    def addLayerColorButton_clicked(self):
        self.set_layer_color_button_color(
            QtWidgets.QColorDialog.getColor(self.selected_color or DEFAULT_LAYER_COLOR)
        )

    def set_layer_color_button_color(self, color):
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

    def move_layer_up(self):
        name = self.sedimental_layer()
        try:
            self.file.move_layer_up(name)
        except (KeyError, ValueError) as e:
            self.message_bar.pushCritical("Impossible to move layer", str(e))
            return
        self.sedimentalLayerComboBox.setCurrentText(name)

    def move_layer_down(self):
        name = self.sedimental_layer()
        try:
            self.file.move_layer_down(name)
        except (KeyError, ValueError) as e:
            self.message_bar.pushCritical("Impossible to move layer", str(e))
            return
        self.sedimentalLayerComboBox.setCurrentText(name)

    def add_layer(self):
        name = self.addLayerNameLineEdit.text()
        color = self.selected_color
        try:
            self.file.add_sedimental_layer(
                name,
                self.sedimental_layer(),
                self.addLayerDeltaBox.value(),
            )
        except (KeyError, ValueError) as e:
            self.message_bar.pushCritical("Impossible to add layer", str(e))
            return
        self.file.set_layer_color(name, color)
        self.sedimentalLayerComboBox.setCurrentText(name)

    def apply_layer(self):
        self.file.set_layer_color(self.sedimental_layer(), self.selected_color)
        self.graphWidget.refresh()

    def extract_layer_z(self):
        processing.run(
            "precourlis:import_layer_from_dem",
            {
                "INPUT": self.layer(),
                "LAYER_NAME": self.sedimental_layer(),
                "DEM": self.extractLayerZDEMComboBox.currentLayer(),
                "BAND": 1,
            },
        )
        self.section_changed(self.sectionComboBox.currentIndex())

    def delete_layer(self):
        self.layer().startEditing()
        layer = self.sedimental_layer()
        self.sedimentalLayerComboBox.setCurrentIndex(
            self.sedimentalLayerComboBox.currentIndex() - 1
        )
        self.file.delete_sedimental_layer(layer)

    def apply_interpolation(self):
        section = self.current_section

        dz0 = self.leftSpinBox.value()
        dz1 = self.rightSpinBox.value()

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
