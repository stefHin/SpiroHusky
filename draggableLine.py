from dataConversion import DataConversion
import logging


class DraggableVLine:

    def __init__(self, ax, parent, plotInfo, color='red', index=0, name="", showValues = True, lineStyle = "--"):
        self.index=index
        self.ax = ax
        self.parent = parent
        self.plotInfo = plotInfo
        self.xAxis = self.plotInfo["x"]
        self.name=name
        self.showValues = showValues
        self.shadedAreas = []

        if self.xAxis == parent.baseTimeParam:
            real_x = parent.shared_x[self.index]
        else:
            real_x = parent.dataConversion.convertFromBaselineParam(self.xAxis, parent.shared_x[self.index], usedParams="smoothedMonotonic")

        #  xmin, xmax = ax.get_xlim()
        #  real_x = xmin + parent.shared_x * (xmax - xmin)

        self.line = ax.axvline(real_x, color=color, linewidth=2, linestyle=lineStyle)

        # --- Add label above the line ---
        self.labels = []   # store multiple text lines

        #factors = [3, 1.7]
        #correctionFactor = 1.0 if self.parent.activeRows >= 3 else factors[self.parent.activeRows-1]

        self.base_y = 1
        self.line_spacing = 0.07 # spacing between lines

        # Name label
        text_label = ax.text(
            real_x,
            self.base_y,
            self.name,
            color=color,
            ha="center",
            va="bottom",
            fontsize=9,
            clip_on=False,
            transform=ax.get_xaxis_transform(),
        )
        self.labels.append(text_label)

        if self.showValues:
            yLabels = {yParamName: parent.dataConversion.convertFromBaselineParam(yParamName, parent.shared_x[self.index], usedParams = "smoothed" if self.parent.use_smoothed_yValues_for_labels.get() else "orig") for yParamName in self.plotInfo["y"]}

            # First line (x value)
            text_x = ax.text(
                real_x,
                self.base_y + self.line_spacing,
                self.getLabelValue(self.xAxis, real_x),
                color="black",
                ha="center",
                va="bottom",
                fontsize=9,
                clip_on=False,
                transform=ax.get_xaxis_transform(),
            )

            self.labels.append(text_x)

            # Additional y lines
            for i, (yLabel, yValue) in enumerate(yLabels.items()):
                yVal = self.base_y + (i + 2) * self.line_spacing
                text_line = ax.text(
                    real_x,
                    yVal,
                    self.getLabelValue(yLabel, yValue),
                    #color=self.plot_lines[i].get_color(),  # match plotted line color
                    color = "blue" if i%2 == 0 else "red",#currently only 2 y-values supported
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    clip_on=False,
                    transform=ax.get_xaxis_transform(),
                )
                self.labels.append(text_line)

        self.press = None

        canvas = self.line.figure.canvas
        self.cid_press = canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = canvas.mpl_connect('motion_notify_event', self.on_motion)

        #self.updatePos()

    def on_press(self, event):
        if event.inaxes not in (self.ax,  getattr(self.ax, "twin", None)):
            return
        
        # another line is already being dragged
        if self.parent.active_line is not None:
            return

        contains, _ = self.line.contains(event)
        if contains:
            self.parent.active_line = self
            self.press = self.line.get_xdata()[0], event.xdata

    def on_motion(self, event):
        if self.parent.active_line is not self:
            return

        if self.press is None or event.inaxes is None:
            return
    
        x0, xpress = self.press
        dx = event.xdata - xpress
        new_x = x0 + dx

        if self.xAxis == self.parent.baseTimeParam:
            self.parent.shared_x[self.index] = new_x
        else:
            self.parent.shared_x[self.index] = self.parent.dataConversion.convertToBaselineParam(self.xAxis, new_x, usedParams="smoothedMonotonic")

        # store shared position
        #xmin, xmax = self.ax.get_xlim()
        #self.parent.shared_x = (new_x - xmin) / (xmax - xmin)

        # move all related lines
        for l in self.parent.draggable_lines_dict[self.name]:
            l.updatePos()

        self.line.figure.canvas.draw_idle()

    def on_release(self, event):
        if self.parent.active_line is self:
            self.parent.active_line = None

        self.press = None

    def disconnect(self):
        canvas = self.line.figure.canvas
        canvas.mpl_disconnect(self.cid_press)
        canvas.mpl_disconnect(self.cid_release)
        canvas.mpl_disconnect(self.cid_motion)
        self.line.remove()
        for lbl in self.labels:
            lbl.remove()

    def updatePos(self):
        if self.xAxis == self.parent.baseTimeParam:
            real_x = self.parent.shared_x[self.index]
        else:
            real_x = self.parent.dataConversion.convertFromBaselineParam(self.xAxis, self.parent.shared_x[self.index], usedParams="smoothedMonotonic")
        self.line.set_xdata([real_x, real_x])

        # Move label

        #name label
        self.labels[0].set_x(real_x)
        self.labels[0].set_y(self.base_y)

        if self.showValues:
            # Update x line
            self.labels[1].set_x(real_x)
            self.labels[1].set_y(self.base_y + self.line_spacing)
            self.labels[1].set_text(self.getLabelValue(self.xAxis, real_x),)

            yLabels = {yParamName: self.parent.dataConversion.convertFromBaselineParam(yParamName, self.parent.shared_x[self.index], usedParams = "smoothed" if self.parent.use_smoothed_yValues_for_labels.get() else "orig") for yParamName in self.plotInfo["y"]}

            # Update y lines
            for i, (yLabel, yValue) in enumerate(yLabels.items()):
                self.labels[i+2].set_x(real_x)
                self.labels[i+2].set_y(self.base_y + (i + 2) * self.line_spacing)
                self.labels[i+2].set_text(self.getLabelValue(yLabel, yValue))


        #self.labels[-1].set_text(f"{self.xAxis}: {real_x:.2f}")

        #xmin, xmax = self.ax.get_xlim()
        #real_x = xmin + self.parent.shared_x * (xmax - xmin)
        #self.line.set_xdata([real_x, real_x])

        for s in self.shadedAreas:
            s.updatePos()


    def addShadedArea(self, shadedArea):
        self.shadedAreas.append(shadedArea)


    def getLabelValue(self, yLabel, yValue):
        if self.parent.calculate_parameter_by_protocol.get() and self.parent.entries["Parameter name"].get() == yLabel:
            startTime = self.safeConvertFromTimeFormat(self.parent.entries["Start time"].get())
            breakBetweenSteps = self.safeConvertFromTimeFormat(self.parent.entries["Break between steps"].get())

            
            try:
                protocol = self.parent.entries["Protocol"].get().split("-")
                if len(protocol) != 3:
                    return "error"

                startIntensity = float(protocol[0])
                increment = float(protocol[1])
                duration = self.convertFromTimeFormat(protocol[2])

                currentXVal = self.parent.shared_x[self.index]

                if currentXVal < startTime:
                    yValue = 0
                elif currentXVal < startTime + duration + breakBetweenSteps:
                    return startIntensity
                else:
                    currentXAfterStart = currentXVal - startTime
                    numberOfStepsCompleted, timeOfCurrentStep = divmod(currentXAfterStart, duration + breakBetweenSteps)
                    fractionOfStepCompleted = min(1, timeOfCurrentStep/duration)
                    yValue = startIntensity + (numberOfStepsCompleted + fractionOfStepCompleted - 1) * increment

            except (TypeError, ValueError, AttributeError):
                return "error"


        digitsAfterComma = self.parent.dataExtraction.paramToDigitsAfterComma[yLabel]

        if digitsAfterComma == "time":
            if self.parent.showTimeParamsInTimeFormat.get():
                total_seconds = int(round(yValue * 60))
                minutes, seconds = divmod(total_seconds, 60)
                roundedValue = f"{minutes}:{seconds:02d}"
            else:
                roundedValue = round(yValue, 2)
        elif digitsAfterComma == 0:
            roundedValue = int(round(yValue))
        else:
            roundedValue = round(yValue, digitsAfterComma)

        if self.parent.showParameterNamesForLabels.get():
            return f"{yLabel}: {roundedValue}"
        else:
            return roundedValue

    @staticmethod
    def safeFloat(val, default=0.0):
        try:
            return float(val.replace(",", "."))
        except (TypeError, ValueError, AttributeError):
            return default

    @staticmethod
    def convertFromTimeFormat(input):
        input = input.replace(",", ".")
        if ":" in input:
            durationParts = input.rsplit(":", 1)
            return float(durationParts[0]) + float(durationParts[1]) / 60.0
        else:
            return float(input)
        
    @staticmethod
    def safeConvertFromTimeFormat(input, default=0.0):
        try:
            return DraggableVLine.convertFromTimeFormat(input)
        except (TypeError, ValueError, AttributeError):
            return default