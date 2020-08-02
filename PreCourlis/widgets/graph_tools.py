from qgis.PyQt import QtCore

from matplotlib.pyplot import Rectangle


class DrawBoxTool(QtCore.QObject):

    released = QtCore.pyqtSignal(float, float, float, float)  # xmin, ymin, xmax, ymax

    def __init__(self, canvas, graph):
        super().__init__(canvas)
        self.canvas = canvas
        self.graph = graph
        self.x0 = None
        self.y0 = None
        self.background = None

    def activate(self):
        self.cidpress = self.canvas.mpl_connect("button_press_event", self.on_press)
        self.cidrelease = self.canvas.mpl_connect(
            "button_release_event", self.on_release
        )
        self.cidmotion = self.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def deactivate(self):
        self.canvas.mpl_disconnect(self.cidpress)
        self.canvas.mpl_disconnect(self.cidrelease)
        self.canvas.mpl_disconnect(self.cidmotion)

    def on_press(self, event):
        if event.button == 1:
            self.x0, self.y0 = event.xdata, event.ydata
            self.rect = Rectangle((event.xdata, event.ydata), 0, 0, fill=False)
            self.graph.add_patch(self.rect)

            # draw everything but the selected rectangle and store the pixel buffer
            self.rect.set_animated(True)
            self.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.graph.bbox)
            self.graph.draw_artist(self.rect)
            self.canvas.blit(self.graph.bbox)

    def on_motion(self, event):
        if event.button == 1:
            x1, y1 = event.xdata, event.ydata
            xmin, ymin, width, height = (
                min(self.x0, x1),
                min(self.y0, y1),
                abs(self.x0 - x1),
                abs(self.y0 - y1),
            )
            self.rect.set_bounds(xmin, ymin, width, height)

            self.canvas.restore_region(self.background)
            self.graph.draw_artist(self.rect)
            self.canvas.blit(self.graph.bbox)

    def on_release(self, event):
        if event.button == 1:
            self.rect.remove()
            self.rect = None
            self.background = None
            self.canvas.draw()

            x1, y1 = event.xdata, event.ydata
            xmin, ymin, xmax, ymax = (
                min(self.x0, x1),
                min(self.y0, y1),
                max(self.x0, x1),
                max(self.y0, y1),
            )
            self.released.emit(xmin, ymin, xmax, ymax)
