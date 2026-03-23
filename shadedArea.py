import logging


class ShadedArea:
    def __init__(self, ax, parent, plotInfo, left_index, right_index, color="green", alpha=0.15):
        self.ax = ax
        self.parent = parent
        self.plotInfo = plotInfo
        self.left_index = left_index
        self.right_index = right_index
        self.color = color
        self.alpha = alpha
        self.xAxis = plotInfo["x"]

        # create span
        x1, x2 = self.get_positions()

        self.patch = ax.axvspan(
            x1,
            x2,
            color=self.color,
            alpha=self.alpha,
            zorder=0
        )

    def get_positions(self):
        """Convert shared baseline positions into axis coordinates."""

        x1 = self.parent.shared_x[self.left_index]
        x2 = self.parent.shared_x[self.right_index]

        if self.xAxis != self.parent.baseTimeParam:
            x1 = self.parent.dataConversion.convertFromBaselineParam(
                self.xAxis, x1, usedParams="smoothedMonotonic"
            )
            x2 = self.parent.dataConversion.convertFromBaselineParam(
                self.xAxis, x2, usedParams="smoothedMonotonic"
            )

        return x1, x2

    def updatePos(self):
        x1, x2 = self.get_positions()

        left = min(x1, x2)
        width = abs(x2 - x1)

        self.patch.set_x(left)
        self.patch.set_width(width)

    def remove(self):
        self.patch.remove()