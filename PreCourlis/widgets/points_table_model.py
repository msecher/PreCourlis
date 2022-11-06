from qgis.PyQt import QtCore

from PreCourlis.core import is_null


class PointsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = None
        self.columns = ["abs_lat", "topo_bat", "zfond"]

    def set_section(self, section):
        self.beginResetModel()
        self.section = section
        self.columns = ["abs_lat", "topo_bat", "zfond"] + section.layer_names
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if self.section is None:
            return 0
        return len(self.section.distances)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if self.section is None:
            return 0
        return len(self.columns)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columns[section]
            if orientation == QtCore.Qt.Vertical:
                return str(section)

    def flags(self, index):
        if index.isValid():
            if index.column() >= 1:
                return (
                    QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsSelectable
                    | QtCore.Qt.ItemIsEditable
                )
            else:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role in (
            QtCore.Qt.DisplayRole,
            QtCore.Qt.EditRole,
        ):
            column = self.columns[index.column()]
            if column == "abs_lat":
                v = self.section.distances[index.row()]
            elif column == "topo_bat":
                v = self.section.topo_bats[index.row()]
            elif column == "zfond":
                v = self.section.z[index.row()]
            else:
                v = self.section.layers_elev[index.column() - 3][index.row()]

        if role == QtCore.Qt.DisplayRole:
            if column == "topo_bat":
                return v
            return str(round(v, 3)) if v is not None else None

        if role == QtCore.Qt.EditRole:
            return v

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.EditRole:
            v = value if not is_null(value) else None

            column = self.columns[index.column()]
            if column == "abs_lat":
                self.section.distances[index.row()] = v
            elif column == "topo_bat":
                self.section.topo_bats[index.row()] = v
            elif column == "zfond":
                self.section.z[index.row()] = v
            else:
                self.section.layers_elev[index.column() - 3][index.row()] = v

            self.dataChanged.emit(index, index, [QtCore.Qt.EditRole])
            return True

        return False
