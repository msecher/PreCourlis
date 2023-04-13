from qgis.core import (
    QgsPoint,
    QgsGeometry,
)
from qgis.PyQt import QtCore

from PreCourlis.core.precourlis_file import PreCourlisFileLine
from PreCourlis.widgets.selection_tool import SelectionTool
from PreCourlis.widgets.zoom_tool import ZoomTool

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class GraphWidget(FigureCanvas):
    editing_finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        self.figure = plt.figure(figsize=(15, 7), constrained_layout=True)
        super().__init__(self.figure)

        self.graph = plt.subplot(111)

        self.selection_tool = SelectionTool(self, self.graph)
        self.selection_tool.activate()

        self.zoom_tool = ZoomTool(self, self.graph)
        self.zoom_tool.activate()

        self.file = None
        self.feature = None
        self.previous_section = None
        self.current_section = None
        self.next_section = None

        self.position = None
        self.pointing_line = None
        self.layers_lines = []
        self.layers_fills = []
        self.legend = None
        self.current_layer_name = None

    def close_figure(self):
        plt.close(self.figure)

    def set_selection_model(self, model):
        self.selection_tool.set_selection_model(model)

    def set_sections(
        self, layer, feature, previous_section, current_section, next_section
    ):
        self.position = None
        self.file = PreCourlisFileLine(layer)
        self.feature = feature
        self.previous_section = previous_section
        self.current_section = current_section
        self.next_section = next_section
        self.refresh()

    def set_current_layer(self, layer_name):
        self.current_layer_name = layer_name
        self.refresh_current_section()
        self.refresh_legend()
        self.draw()

    def axis_position(self, section):
        """
        Return linear referencing of axis intersection for passed section.
        """
        f = section.feature
        intersection = QgsGeometry(
            QgsPoint(f.attribute("axis_x"), f.attribute("axis_y"))
        )
        return f.geometry().lineLocatePoint(intersection)

    def draw_section(self, section, offset, **kwargs):
        if section.distances[0] is None:
            return
        return self.graph.plot(
            [d + offset for d in section.distances],
            section.z,
            label=section.name,
            **kwargs,
        )

    def clear(self):
        self.graph.clear()
        self.pointing_line = None
        self.layers_lines = []
        self.layers_fills = []
        self._legend = None

    def refresh(self):
        self.clear()

        axis_pos = self.axis_position(self.current_section)

        if self.previous_section:
            self.draw_section(
                self.previous_section,
                axis_pos - self.axis_position(self.previous_section),
                color="green",
                linewidth=0.5,
            )

        self.refresh_current_section(False)

        if self.next_section:
            self.draw_section(
                self.next_section,
                axis_pos - self.axis_position(self.next_section),
                color="blue",
                linewidth=0.5,
            )

        # Draw axis position
        self.graph.axvline(axis_pos, color="black")

        self.graph.grid(True)
        self.graph.set_ylabel("Z (m)")
        self.graph.set_xlabel("Abscisse en travers (m)")

        self.refresh_legend()

        self.draw()

    def refresh_legend(self):
        if self.legend is not None:
            self.legend.remove()
        lines, labels = self.graph.get_legend_handles_labels()
        self.legend = self.graph.legend(
            lines,
            labels,
            bbox_to_anchor=(1, 0.5),
            loc="center left",
            fancybox=True,
            shadow=True,
            prop={"size": 10},
        )

    def refresh_current_section(self, draw=True):
        [line.remove() for line in self.layers_lines]
        self.layers_lines = []

        [poly.remove() for poly in self.layers_fills]
        self.layers_fills = []

        section = self.current_section
        if section is None:
            return
        if section.distances[0] is None:
            return

        previous_values = None
        current_column = None
        for i, layer in enumerate(["zfond"] + section.layer_names):
            if layer == "zfond":
                values = self.current_section.z
            else:
                values = section.layers_elev[i - 1]

            color = self.file.layer_color(layer)

            if previous_values is not None:
                self.layers_fills.append(
                    self.graph.fill_between(
                        section.distances,
                        previous_values,
                        values,
                        where=values <= previous_values,
                        facecolor=color,
                        alpha=0.3,
                    )
                )
            previous_values = values

            (line,) = self.graph.plot(
                section.distances,
                values,
                label=layer,
                color=color,
                marker="." if self.current_layer_name == layer else None,
                zorder=10 if self.current_layer_name == layer else 1,
            )
            self.layers_lines.append(line)

            if self.current_layer_name == layer:
                current_column = i + 1

        self.selection_tool.set_data(
            section.distances,
            [section.z] + list(section.layers_elev),
            current_column,
        )

        if draw:
            self.draw()
