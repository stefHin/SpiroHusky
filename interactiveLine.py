import matplotlib.pyplot as plt
import numpy as np
import uuid
import logging


class InteractiveLine:
    def __init__(self, ax, parent, plotName, plotInfo, color=None, xData=None, yData=None, id=None):
        self.ax = ax
        self.color = color
        self.parent = parent
        self.plotInfo = plotInfo
        self.plotName = plotName
        self.id = str(uuid.uuid4()) if id is None else id

        # State variables
        self.start = None     # First click (x0, y0)
        self.line = None      # Matplotlib Line2D object
        self.dragging = False # Whether we're dragging an existing line
        self.press = None     # For dragging

        if (xData is not None and yData is not None):
            self.line, = self.ax.plot(xData, yData, color=self.color if self.color is not None else "#00C9EC", linestyle="--", linewidth=2)
            self.dragging = True

        # Connect events
        self.cid_press = ax.figure.canvas.mpl_connect("button_press_event", self.on_press)
        self.cid_release = ax.figure.canvas.mpl_connect("button_release_event", self.on_release)
        self.cid_motion = ax.figure.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def on_press(self, event):
        #if self.parent.active_line is not None and self.parent.active_line is not self:
        #    return

        if self.line is None:
            # Only respond to right mouse button
            if event.button != 3 or not self.ax.bbox.contains(event.x, event.y):
                return

            if self.color is None:
                self.color = self.parent.line_color

            # convert mouse position to this axis' data coordinates
            x_mouse, y_mouse = self.ax.transData.inverted().transform((event.x, event.y))

            # First click: start drawing a new line
            self.start = (x_mouse, y_mouse)

            # Create a line with the start point duplicated
            self.line, = self.ax.plot(
                [x_mouse, x_mouse],
                [y_mouse, y_mouse],
                color=self.color,
                linestyle="--",
                linewidth=2
            )

            self.parent.active_line = self
            self.ax.figure.canvas.draw_idle()

        else:
            # Second click: finalize line
            if self.dragging == False:
                # add new potential line
                potential_interactive_line = InteractiveLine(self.ax, self.parent, self.plotName, self.plotInfo)
                self.parent.interactive_lines.append(potential_interactive_line)
            elif event.button == 2 and self.ax.bbox.contains(event.x, event.y) and self.line.contains(event)[0]:
                # destroy line
                if self.line is not None:
                    self.line.remove()
                    self.ax.figure.canvas.draw_idle()
                self.disconnect()
                return

            self.start = None
            self.dragging = True

            # convert mouse position to this axis' coordinates
            x_mouse, y_mouse = self.ax.transData.inverted().transform((event.x, event.y))

            # Check if click is on the line
            contains, _ = self.line.contains(event)
            if contains and self.parent.active_line is not self:
                self.parent.active_line = self
                self.press = (x_mouse, y_mouse)

    def on_motion(self, event):
        #if self.parent.active_line is not self:
        #    return

        if not self.ax.bbox.contains(event.x, event.y):#event.inaxes != self.ax:
            return
        
        # convert mouse position to this axis' data coordinates
        x_mouse, y_mouse = self.ax.transData.inverted().transform((event.x, event.y))


        if self.start is not None:
            # Line is being drawn: update end point to follow mouse
            x0, y0 = self.start
            #x1, y1 = event.xdata, event.ydata
            #self.line.set_data([x0, x1], [y0, y1])
            self.line.set_data([x0, x_mouse], [y0, y_mouse])
            self.ax.figure.canvas.draw_idle()

        elif self.dragging and self.press is not None and self.parent.active_line is self:
            # Dragging the line
            xpress, ypress = self.press
            dx = x_mouse - xpress
            dy = y_mouse - ypress
            xdata, ydata = self.line.get_data()
            self.line.set_data([x + dx for x in xdata],
                               [y + dy for y in ydata])
            #self.press = (event.xdata, event.ydata)
            self.press = (x_mouse, y_mouse)
            self.ax.figure.canvas.draw_idle()

    def on_release(self, event):
        # Stop dragging
        if self.parent.active_line is self:
            self.parent.active_line = None
        self.press = None

    def disconnect(self):
        self.ax.figure.canvas.mpl_disconnect(self.cid_press)
        self.ax.figure.canvas.mpl_disconnect(self.cid_release)
        self.ax.figure.canvas.mpl_disconnect(self.cid_motion)
        self.line = None
        if self.parent.active_line is self:
            self.parent.active_line = None