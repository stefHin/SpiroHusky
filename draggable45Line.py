import numpy as np
import matplotlib.pyplot as plt
import logging


class Draggable45Line:

    def __init__(self, ax, parent, plotName, plotInfo, name="V-slope", color="#800080"):
        self.ax = ax
        self.parent = parent
        self.name = name
        self.plotName = plotName

        xLim = np.array(ax.get_xlim())
        yLim = np.array(ax.get_ylim())

        self.limit = min(xLim[1], yLim[1])

        if not plotName in parent.bisectingLinesXDict:
            self.parent.bisectingLinesXDict[plotName] = self.limit * 2/3

        offset = self.parent.bisectingLinesXDict[self.plotName] * -1 if self.parent.bisectingLinesXDict[self.plotName] < 0 else 0

        x_vals = np.array([self.parent.bisectingLinesXDict[self.plotName] + offset, self.limit - offset])
        y_vals = np.array([0 + offset, self.limit - self.parent.bisectingLinesXDict[self.plotName] - offset])

        self.line = ax.plot(
            x_vals,
            y_vals,
            "--",
            color=color,
            linewidth=2
        )[0]

        self.press = None

        canvas = self.line.figure.canvas
        self.cid_press = canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if self.parent.active_line is not None:
            return

        contains, _ = self.line.contains(event)
        if contains:
            self.parent.active_line = self
            self.press = (event.xdata, event.ydata)
            self.startX0 = self.parent.bisectingLinesXDict[self.plotName]

    def on_motion(self, event):
        if self.parent.active_line is not self:
            return
        if self.press is None or event.xdata is None:
            return

        # get the mouse position in pixels
        xpix, ypix = event.x, event.y

        # transform from figure pixels to primary axis data coordinates
        xdata, ydata = self.ax.transData.inverted().transform((xpix, ypix))


        #xpress, ypress = self.press
        #dx = event.xdata - xpress
        #dy = -event.ydata + ypress

        #logging.info(f"{xpress}, {ypress}")

        #self.x0 = self.startX0 + dx - dy
        #self.press = (event.xdata, event.ydata)
        self.parent.bisectingLinesXDict[self.plotName] = xdata - ydata

        self.updatePos()
        self.line.figure.canvas.draw_idle()

    def on_release(self, event):
        if self.parent.active_line is self:
            self.parent.active_line = None
        self.press = None

    def updatePos(self):
        x_vals = np.array([self.parent.bisectingLinesXDict[self.plotName], self.limit])
        y_vals = np.array([0, self.limit - self.parent.bisectingLinesXDict[self.plotName]])

        self.line.set_data(x_vals, y_vals)

    def disconnect(self):
        canvas = self.line.figure.canvas
        canvas.mpl_disconnect(self.cid_press)
        canvas.mpl_disconnect(self.cid_release)
        canvas.mpl_disconnect(self.cid_motion)
        self.line.remove()