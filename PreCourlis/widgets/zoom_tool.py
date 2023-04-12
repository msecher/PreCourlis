from matplotlib.transforms import Bbox


class ZoomTool:
    def __init__(self, canvas, graph):
        self.canvas = canvas
        self.graph = graph
        self.drag_started_bbox = None
        self.drag_started_point = None

    def activate(self):
        self.cidpress = self.canvas.mpl_connect("button_press_event", self.on_press)
        self.cidrelease = self.canvas.mpl_connect(
            "button_release_event", self.on_release
        )
        self.cidmotion = self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.cidscroll = self.canvas.mpl_connect("scroll_event", self.on_scroll)

    def deactivate(self):
        self.canvas.mpl_disconnect(self.cidscroll)

    def on_press(self, event):
        if event.button == 2:
            self.graph.start_pan(event.x, event.y, 1)
        if event.button == 3:
            self.apply_bbox(self.limits())

    def on_motion(self, event):
        if event.button == 2:
            self.graph.drag_pan(1, event.key, event.x, event.y)
            self.canvas.draw_idle()

    def on_release(self, event):
        if event.button == 2:
            self.graph.end_pan()
            self.canvas.toolbar.push_current()

    def on_scroll(self, event):
        if event.xdata is None or event.ydata is None:
            return
        self.zoom_by_factor(1.5**event.step, event.xdata, event.ydata)
        self.canvas.toolbar.push_current()

    def center(self):
        xlim = self.graph.get_xlim()
        ylim = self.graph.get_ylim()
        return (xlim[0] + xlim[1]) / 2, (ylim[0] + ylim[1]) / 2

    def width(self):
        xlim = self.graph.get_xlim()
        return xlim[1] - xlim[0]

    def height(self):
        ylim = self.graph.get_ylim()
        return ylim[1] - ylim[0]

    def current_bbox(self):
        xlim = self.graph.get_xlim()
        ylim = self.graph.get_ylim()
        return Bbox.from_extents(xlim[0], ylim[0], xlim[1], ylim[1])

    def constrained_bbox(self, bbox, limits):
        """Adjust bbox in limits"""
        xmin = bbox.xmin
        ymin = bbox.ymin
        xmax = bbox.xmax
        ymax = bbox.ymax

        if xmin < limits.xmin:
            xmax += limits.xmin - xmin
            xmin = limits.xmin

        if ymin < limits.ymin:
            ymax += limits.ymin - ymin
            ymin = limits.ymin

        if xmax > limits.xmax:
            xmin += limits.xmax - xmax
            xmax = limits.xmax

        if ymax > limits.ymax:
            ymin += limits.ymax - ymax
            ymax = limits.ymax

        return Bbox.from_extents(xmin, ymin, xmax, ymax)

    def translated_bbox(self, bbox, dx, dy):
        """Translate bbox by dx and dy"""
        return Bbox.from_extents(
            bbox.xmin + dx,
            bbox.ymin + dy,
            bbox.xmax + dx,
            bbox.ymax + dy,
        )

    def limits(self):
        """Return limits Bbox for zooming and dragging regarding data limits and margins"""
        dataLim = self.graph.dataLim
        margins = self.graph.margins()
        return Bbox.from_extents(
            dataLim.xmin - dataLim.width * margins[0],
            dataLim.ymin - dataLim.height * margins[1],
            dataLim.xmax + dataLim.width * margins[0],
            dataLim.ymax + dataLim.height * margins[1],
        )

    def apply_bbox(self, bbox):
        """Apply bbox on graph and redraw canvas"""
        self.graph.set_xlim(bbox.xmin, bbox.xmax)
        self.graph.set_ylim(bbox.ymin, bbox.ymax)
        self.canvas.draw()

    def zoom_by_factor(self, factor, x, y):
        """Zoom by factor around point defined by x, y coordinates"""
        # Compute ratios around x,y
        current_bbox = self.current_bbox()
        left = (x - current_bbox.xmin) / current_bbox.width
        right = (current_bbox.xmax - x) / current_bbox.width
        bottom = (y - current_bbox.ymin) / current_bbox.height
        top = (current_bbox.ymax - y) / current_bbox.height

        # Apply zoom factor on sizes
        width, height = self.width() / factor, self.height() / factor
        limits = self.limits()
        if width > limits.width:
            width = limits.width
        if height > limits.height:
            height = limits.height

        # Apply new sizes with same ratios around x,y
        bbox = Bbox.from_extents(
            x - left * width,
            y - bottom * height,
            x + right * width,
            y + top * height,
        )

        self.apply_bbox(self.constrained_bbox(bbox, limits))
