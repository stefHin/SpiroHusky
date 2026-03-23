import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import math
import numpy as np
from dataPlotter import DataPlotter
from draggableLine import DraggableVLine
from shadedArea import ShadedArea
from draggable45Line import Draggable45Line
from interactiveLine import InteractiveLine
from tkcolorpicker import askcolor
from matplotlib.backends.backend_pdf import PdfPages
from tkinter import simpledialog
import json
from tkinter import filedialog
import copy
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from tkinter import simpledialog
from collections import OrderedDict
import os
from datetime import datetime
import logging
import zipfile

class PlotGUI:
    def __init__(self, root, dataExtraction, plotInfos, dataConversion, xmlFile, file_dir_path, spiroFileContent = None, spiroFileName = None):
        self.dataExtraction = dataExtraction
        self.root = root
        self.dataDictionary = dataExtraction.dataDictionary
        self.plotInfos = plotInfos  # list of plot names
        self.plot_check_vars = {}  # tk.IntVar for each checkbox
        self.dataPlotter = DataPlotter(self.dataExtraction)
        self.dataConversion = dataConversion
        self.active_line = None
        self.xmlFile = xmlFile
        self.file_dir_path = file_dir_path

        if spiroFileName:
            self.suggestedFileName = os.path.splitext(spiroFileName)[0].replace(".", "_")
        else:
            self.suggestedFileName = os.path.splitext(xmlFile)[0].replace(".", "_")

        #-------------------------------------------------
        # Sidebar container (canvas + scrollbar)
        # ---------- Sidebar container ----------
        SIDEBAR_BG = "#eef2f7"   # soft modern gray-blue

        self.check_canvas = tk.Canvas(
            root,
            width=260,
            bg=SIDEBAR_BG,
            highlightthickness=0
        )
        self.check_scrollbar = tk.Scrollbar(root, orient="vertical", command=self.check_canvas.yview)


        self.check_canvas.pack(side=tk.RIGHT, fill=tk.Y)
        self.check_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.check_canvas.configure(yscrollcommand=self.check_scrollbar.set)

        self.check_frame = tk.Frame(self.check_canvas, bg=SIDEBAR_BG)
        self.check_canvas.create_window((0, 0), window=self.check_frame, anchor="nw", width=260)

        def on_frame_configure(event):
            self.check_canvas.configure(scrollregion=self.check_canvas.bbox("all"))

        self.check_frame.bind("<Configure>", on_frame_configure)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # scrolling 

        def _on_mousewheel(event):
            # Windows / Mac
            self.check_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            # Linux
            if event.num == 4:
                self.check_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.check_canvas.yview_scroll(1, "units")

        # Bind globally
        self.root.bind_all("<MouseWheel>", _on_mousewheel)   # Windows / Mac
        self.root.bind_all("<Button-4>", _on_mousewheel_linux)  # Linux scroll up
        self.root.bind_all("<Button-5>", _on_mousewheel_linux)  # Linux scroll down

        # ---------- Helpers ----------
        SECTION_PADY = (12, 4)

        def section_label(parent, text):
            return tk.Label(parent, text=text, bg=SIDEBAR_BG, fg="#2c3e50",
                            font=("Segoe UI", 10, "bold"))

        def styled_button(parent, text, command):
            return tk.Button(parent, text=text, command=command,
                            relief="flat", bg="#dfe6ee", activebackground="#cfd8e3",
                            padx=8, pady=3)

        def primary_button(parent, text, command, backgroundColor="#D32F2F"):
            active_bg = darken_color(backgroundColor, 0.85)

            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=backgroundColor,
                fg="white",
                activebackground=active_bg,
                activeforeground="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                padx=10,
                pady=6
            )
    
        def darken_color(hex_color, factor=0.85):
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)

            return f"#{r:02x}{g:02x}{b:02x}"

        def clean_checkbutton(parent, text, var, cmd):
            return tk.Checkbutton(
                parent,
                text=text,
                variable=var,
                command=cmd,
                bg=SIDEBAR_BG,
                activebackground=SIDEBAR_BG,
                highlightthickness=0,
                bd=0
            )


        # ---------- Plots ----------
        section_label(self.check_frame, "Plots").pack(anchor="w", padx=10, pady=SECTION_PADY)

        for plot_name in plotInfos.keys():
            var = tk.BooleanVar(value=True)
            chk = clean_checkbutton(self.check_frame, plot_name, var, self.update_plots)
            chk.pack(anchor="w", padx=15)
            self.plot_check_vars[plot_name] = var


        # ---------- Select buttons ----------
        self.button_frame = tk.Frame(self.check_frame, bg=SIDEBAR_BG)
        self.button_frame.pack(anchor='w', padx=10, pady=(8, 10))

        self.select_all_btn = styled_button(self.button_frame, "Select All", self.select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=2)

        self.deselect_all_btn = styled_button(self.button_frame, "Clear", self.deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=2)


        # ---------- Display ----------
        section_label(self.check_frame, "Display").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.show_major_background_lines = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Major background lines",
                        self.show_major_background_lines, self.update_plots).pack(anchor="w", padx=15)
        
        self.show_minor_background_lines = tk.BooleanVar(value=False)
        clean_checkbutton(self.check_frame, "Minor background lines",
                        self.show_minor_background_lines, self.update_plots).pack(anchor="w", padx=15)

        self.fixed_ratio = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Fixed x:y ratio",
                        self.fixed_ratio, self.on_ratio_toggle).pack(anchor="w", padx=15)

        self.ratio_var = tk.DoubleVar(value=1.5)

        self.ratio_slider = tk.Scale(
            self.check_frame,
            from_=0.2, to=3.0, resolution=0.01,
            orient=tk.HORIZONTAL,
            label="Ratio",
            variable=self.ratio_var,
            bg=SIDEBAR_BG,
            highlightthickness=0,
            bd=0
        )
        self.ratio_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.ratio_slider.pack(fill=tk.X, padx=15, pady=(0, 8))


        # ---------- Labels ----------
        section_label(self.check_frame, "Labels").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.use_smoothed_yValues_for_labels = tk.BooleanVar(value=False)
        clean_checkbutton(self.check_frame, "Use smoothed values",
                        self.use_smoothed_yValues_for_labels,
                        self.update_plots).pack(anchor="w", padx=15)

        self.showParameterNamesForLabels = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Show parameter names",
                        self.showParameterNamesForLabels,
                        self.update_plots).pack(anchor="w", padx=15)

        self.showTimeParamsInTimeFormat = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Show time as mm:ss",
                        self.showTimeParamsInTimeFormat,
                        self.update_plots).pack(anchor="w", padx=15)


        # ---------- Thresholds ----------
        section_label(self.check_frame, "Thresholds").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.show_ventilatory_thresholds = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Show VTs",
                        self.show_ventilatory_thresholds,
                        self.update_plots).pack(anchor="w", padx=15)

        self.show_values_for_ventilatory_thresholds = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Show VT values",
                        self.show_values_for_ventilatory_thresholds,
                        self.update_plots).pack(anchor="w", padx=15)


        # ---------- Zones ----------
        section_label(self.check_frame, "Training Zones").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.num_of_zones = tk.IntVar(value=5)

        self.num_of_zones_slider = tk.Scale(
            self.check_frame,
            from_=3, to=7, resolution=1,
            orient=tk.HORIZONTAL,
            label="Number of zones (3–7)",
            variable=self.num_of_zones,
            bg=SIDEBAR_BG,
            highlightthickness=0,
            bd=0
        )
        self.num_of_zones_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.num_of_zones_slider.pack(fill=tk.X, padx=15, pady=(0, 8))

        self.show_training_zones = tk.BooleanVar(value=False)
        clean_checkbutton(self.check_frame, "Show zones",
                        self.show_training_zones,
                        self.update_plots).pack(anchor="w", padx=15)

        self.show_values_for_training_zones = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Show values",
                        self.show_values_for_training_zones,
                        self.update_plots).pack(anchor="w", padx=15)

        self.show_shading_for_training_zones = tk.BooleanVar(value=True)
        clean_checkbutton(self.check_frame, "Show shading",
                        self.show_shading_for_training_zones,
                        self.update_plots).pack(anchor="w", padx=15, pady=(0, 8))

        self.transparency_var = tk.DoubleVar(value=0.3)

        self.transparency_slider = tk.Scale(
            self.check_frame,
            from_=0, to=1, resolution=0.01,
            orient=tk.HORIZONTAL,
            label="Transparency",
            variable=self.transparency_var,
            bg=SIDEBAR_BG,
            highlightthickness=0,
            bd=0
        )
        self.transparency_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.transparency_slider.pack(fill=tk.X, padx=15)


        # ---------- Additional lines ----------
        section_label(self.check_frame, "Additional Lines").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.line_frame = tk.Frame(self.check_frame, bg=SIDEBAR_BG)
        self.line_frame.pack(fill=tk.X, padx=15)

        self.show_additional_lines = tk.BooleanVar(value=True)
        clean_checkbutton(self.line_frame, "Show additional lines",
                        self.show_additional_lines,
                        self.update_plots).pack(side=tk.LEFT)

        self.line_color = (
            self.dataExtraction.config
                .get("lineColor", {})
                .get("interactiveLines", "#00C9EC")
        )

        self.color_button = styled_button(self.line_frame, "Color", self.choose_line_color)
        self.color_button.configure(bg=self.line_color)
        self.color_button.pack(side=tk.LEFT, padx=8)


        # ---------- Parameter ----------
        section_label(self.check_frame, "Step Protocol Utilities").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.line_frame2 = tk.Frame(self.check_frame, bg=SIDEBAR_BG)
        self.line_frame2.pack(fill=tk.X, padx=15)

        self.calculate_parameter_by_protocol = tk.BooleanVar(value=False)

        clean_checkbutton(self.line_frame2, "Calculate parameter",
                        self.calculate_parameter_by_protocol,
                        self.update_plots).pack(side=tk.LEFT)

        self.update_button = styled_button(self.line_frame2, "Update", self.update_plots)
        self.update_button.pack(side=tk.LEFT, padx=8)


        # ---------- Form ----------

        self.form_frame = tk.Frame(self.check_frame, bg=SIDEBAR_BG)
        self.form_frame.pack(fill=tk.X, padx=15)

        fields = ["Parameter name", "Start time", "Protocol", "Break between steps"]
        self.entries = {}
        self.entry_vars = {}

        for i, field in enumerate(fields):
            tk.Label(self.form_frame, text=field + ":", bg=SIDEBAR_BG).grid(row=i, column=0, sticky="w", pady=4)

            var = tk.StringVar()
            entry = tk.Entry(self.form_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky="ew", pady=4)

            self.entries[field] = entry
            self.entry_vars[field] = var

        self.form_frame.columnconfigure(1, weight=1)

        # ---------- Notes ----------
        section_label(self.check_frame, "Notes").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.notes_text = tk.Text(
            self.check_frame,
            height=3,
            wrap="word",
            bg="white",
            relief="solid",
            bd=1
        )
        self.notes_text.pack(fill=tk.X, padx=15, pady=(0, 8))

        # Auto-grow on typing
        self.notes_text.bind("<KeyRelease>", self.auto_resize_text)


        # ---------- Snapshots ----------
        section_label(self.check_frame, "Snapshots").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.snapshots = OrderedDict()
        self.snapshot_vars = {}  # for "add to pdf"

        # container
        self.snapshot_container = tk.Frame(self.check_frame, bg=SIDEBAR_BG)
        self.snapshot_container.pack(fill=tk.X, padx=10)

        # buttons row
        snap_btn_frame = tk.Frame(self.check_frame, bg=SIDEBAR_BG)
        snap_btn_frame.pack(fill=tk.X, padx=10, pady=(5, 5))

        styled_button(snap_btn_frame, "Save Snapshot", self.save_snapshot).pack(side=tk.LEFT, padx=2)

        # ---------- Export ----------

        section_label(self.check_frame, "Data Export").pack(anchor="w", padx=10, pady=SECTION_PADY)

        self.save_to_file_btn = primary_button(self.check_frame, "💾 Save to File", self.save_to_file, backgroundColor="#2F5BD3")
        self.save_to_file_btn.pack(fill=tk.X, padx=15, pady=(0, 7))

        self.export_btn = primary_button(self.check_frame, "📄 Export PDF", self.export_pdf, backgroundColor="#D32F2F")
        self.export_btn.pack(fill=tk.X, padx=15, pady=(0, 7))

        self.export_png_btn = primary_button(self.check_frame, "🖼️ Export PNGs", self.export_pngs, backgroundColor="#198B28")
        self.export_png_btn.pack(fill=tk.X, padx=15, pady=(0, 7))


        # ---------- Plot frame ----------
        self.plot_frame = tk.Frame(root)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            #-------------------------------------------------------


        self.baseTimeParam = self.dataExtraction.config["baseTimeParam"]
        self.baseTimeValues = self.dataDictionary[self.baseTimeParam]
        self.draggable_lines = []
        self.shared_x = []
        # VT1, VT2
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)/3)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*2/3)])

        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.2)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.3)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.4)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.5)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.6)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.7)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.8)])
        self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.9)])

        # for additional angle bisecting lines
        #for i in range(len(plotInfos)):
        #    self.shared_x.append(self.baseTimeValues[int(len(self.baseTimeValues)*0.75)])

        self.bisectingLinesXDict = {}

        self.xRefPoint = self.baseTimeValues[int(len(self.baseTimeValues)*0.65)]


        self.zone_colors = [
            [
            "#7DCEA0",  # Z1 - green (endurance)
            "#F4D03F",  # Z2 - yellow (tempo)
            "#E74C3C",  # Z3 - red (VO2max)
            ],
            [
            "#7DCEA0",  # Z1 - green (endurance)
            "#F4D03F",  # Z2 - yellow (tempo)
            "#EB984E",  # Z3 - orange (threshold)
            "#E74C3C",  # Z4 - red (VO2max)
            ],
            [
            "#2E86DE",  # Z1 - deep blue (very easy / recovery)
            "#7DCEA0",  # Z2 - green (endurance)
            "#F4D03F",  # Z3 - yellow (tempo)
            "#EB984E",  # Z4 - orange (threshold)
            "#E74C3C",  # Z5 - red (VO2max)
            ],
            [
            "#2E86DE",  # Z1 - deep blue (very easy / recovery)
            "#7DCEA0",  # Z2 - green (endurance)
            "#F4D03F",  # Z3 - yellow (tempo)
            "#EB984E",  # Z4 - orange (threshold)
            "#E74C3C",  # Z5 - red (VO2max)
            "#8E44AD"   # Z6 - purple (anaerobic / max)
            ],
            [
            "#2E86DE",  # Z1 - deep blue (very easy / recovery)
            "#48C9B0",  # Z2 - teal (easy aerobic)
            "#7DCEA0",  # Z3 - green (endurance)
            "#F4D03F",  # Z4 - yellow (tempo)
            "#EB984E",  # Z5 - orange (threshold)
            "#E74C3C",  # Z6 - red (VO2max)
            "#8E44AD"   # Z7 - purple (anaerobic / max)
        ]]

        self.vt_line_color =  (
            self.dataExtraction.config
                .get("lineColor", {})
                .get("thresholds", "#189200")
        )

        self.zones_line_color =  (
            self.dataExtraction.config
                .get("lineColor", {})
                .get("zones", "#926B00")
        )

        self.angleBisectors_line_color =  (
            self.dataExtraction.config
                .get("lineColor", {})
                .get("angleBisectors", "#800080")
        )

        self.old_interactive_lines_dict = {}
        self.interactive_lines = []

        self.on_ratio_toggle()

        if spiroFileContent:
            self.load_from_file_content(spiroFileContent)
        #self.update_plots()

    def on_ratio_toggle(self, updatePlots=True):
        if self.fixed_ratio.get():
            self.ratio_slider.configure(state=tk.NORMAL)
        else:
            self.ratio_slider.configure(state=tk.DISABLED)

        if updatePlots:
            self.update_plots()

    def on_slider_release(self, event):
        self.update_plots()

    def select_all(self):
        for var in self.plot_check_vars.values():
            var.set(True)
        self.update_plots()

    def deselect_all(self):
        for var in self.plot_check_vars.values():
            var.set(False)
        self.update_plots()

    def capture_line_state(self):
        for line in self.interactive_lines:
            if line.line is not None:
                xdata, ydata = line.line.get_data()
                self.old_interactive_lines_dict.setdefault(line.plotName, {})[line.id] = {
                    "x": xdata.copy(),
                    "y": ydata.copy(),
                    "color": line.color,
                    "plotInfo": line.plotInfo,
                    "id": line.id
                }


    def clear_lines(self):
        # remove old draggable lines cleanly
        if hasattr(self, "draggable_lines"):
            for line in self.draggable_lines:
                line.disconnect()
        
        if hasattr(self, "shaded_areas"):
            for area in self.shaded_areas:
                area.remove()

        if hasattr(self, "draggable_45_lines"):
            for line in self.draggable_45_lines:
                line.disconnect()
        
        if hasattr(self, "interactive_lines"):
            for line in self.interactive_lines:
                line.disconnect()

        self.draggable_lines = []
        self.zone_lines = []
        self.shaded_areas = []

        self.draggable_lines_dict = {}

        self.draggable_45_lines = []
        self.interactive_lines = []

    def update_plots(self, captureLineState = True):
        if captureLineState:
            self.capture_line_state()

        # Clear old plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        plt.close('all')  # closes all open figures

        # Get selected plots
        selected = [name for name, var in self.plot_check_vars.items() if var.get() == 1]
        n = len(selected)
        if n == 0:
            return

        # Determine grid size (square-ish)
        cols = math.ceil(n**0.5)  # max 2 columns
        rows = (n + cols - 1) // cols  # ceiling division
        self.activeRows = rows
        self.activeCols = cols

        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n == 1:
            axes = [[axes]]  # make it 2D for consistent indexing
        elif rows == 1:
            axes = [axes]  # single row

        axes_flat = [ax for row in axes for ax in (row if isinstance(row, (list, tuple, np.ndarray)) else [row])]

        self.clear_lines()

        # Create each plot
        additionalLineCounter = 0
        for ax, plot_name in zip(axes_flat, selected):
            self.createPlot(plot_name, ax, cols)

            if self.show_ventilatory_thresholds.get():
                vt1_line = DraggableVLine(ax, self, self.plotInfos[plot_name], color=self.vt_line_color, index=0, name="VT1", showValues=self.show_values_for_ventilatory_thresholds.get(), lineStyle="--")
                self.draggable_lines.append(vt1_line)
                self.draggable_lines_dict.setdefault("VT1", []).append(vt1_line)

                vt2_line = DraggableVLine(ax, self, self.plotInfos[plot_name], color=self.vt_line_color, index=1, name="VT2", showValues=self.show_values_for_ventilatory_thresholds.get(), lineStyle="--")
                self.draggable_lines.append(vt2_line)
                self.draggable_lines_dict.setdefault("VT2", []).append(vt2_line)
            
            if self.show_training_zones.get():
                zone_lines_of_plot = []
                for i in range(self.num_of_zones.get()+1):
                    lineName=self.getTrainingZoneVerticalLineName(i, self.num_of_zones.get())
                    zone_line = DraggableVLine(ax, self, self.plotInfos[plot_name], color=self.zones_line_color, index=self.getTrainingZoneIndex(i, self.num_of_zones.get())+2, name=lineName, showValues=self.show_values_for_training_zones.get(), lineStyle=":")
                    self.zone_lines.append(zone_line)
                    self.draggable_lines.append(zone_line)
                    self.draggable_lines_dict.setdefault(lineName, []).append(zone_line)
                    zone_lines_of_plot.append(zone_line)
                
                # create shaded zones
                if self.show_shading_for_training_zones.get():
                    for i in range(self.num_of_zones.get()):
                        left_index = self.getTrainingZoneIndex(i, self.num_of_zones.get()) + 2
                        right_index = self.getTrainingZoneIndex(i, self.num_of_zones.get()) + 3

                        shaded = ShadedArea(
                            ax,
                            self,
                            self.plotInfos[plot_name],
                            left_index,
                            right_index,
                            color=self.zone_colors[self.num_of_zones.get()-3][i],
                            alpha=self.transparency_var.get()
                        )
                        zone_lines_of_plot[i].addShadedArea(shaded)
                        zone_lines_of_plot[i+1].addShadedArea(shaded)

                        self.shaded_areas.append(shaded)

            if self.show_additional_lines.get():
                if self.plotInfos[plot_name].get("angleBisector", False):
                    angleBisector = Draggable45Line(ax, self, plot_name, self.plotInfos[plot_name], color=self.angleBisectors_line_color)
                    self.draggable_45_lines.append(angleBisector)
                    #lineName=f"additionalLine{additionalLineCounter}"
                    #additionalLine = DraggableVLine(ax, self, self.plotInfos[plot_name], color="#009286", index=additionalLineCounter+9, name=lineName, showValues=False, lineStyle="--", angleBisector=True)
                    #self.draggable_lines.append(additionalLine)
                    #self.draggable_lines_dict.setdefault(lineName, []).append(additionalLine)
                    #additionalLineCounter+=1

                for old_line in self.old_interactive_lines_dict.get(plot_name, {}).values():
                    new_line = InteractiveLine(ax, self, plot_name, self.plotInfos[plot_name], color=old_line["color"], xData=old_line["x"], yData=old_line["y"], id=old_line["id"])
                    #new_line.line.set_data(old_line["x"], old_line["y"])
                    self.interactive_lines.append(new_line)

                self.old_interactive_lines_dict.pop(plot_name, None)

                potential_interactive_line = InteractiveLine(ax, self, plot_name, self.plotInfos[plot_name])
                self.interactive_lines.append(potential_interactive_line)


            if self.fixed_ratio.get():
                ax.set_box_aspect(1/self.ratio_var.get())   # for 16:9 subplot ratio


        # Hide extra axes if any
        for ax in axes_flat[len(selected):]:
            ax.set_visible(False)

        # Embed figure in Tkinter
        fig.tight_layout(pad=2.5, h_pad=5.5, w_pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def getTrainingZoneVerticalLineName(self, index, numOfZones):
        if index == 0:
            return "Z1"
        elif index == numOfZones:
            return f"Z{numOfZones}"
        else:
            return f"Z{index}-{index+1}"
        
    def getTrainingZoneIndex(self, index, numOfZones):
        match numOfZones:
            case 3:
                return index + 2
            case 4:
                return index + 2
            case 5:
                return index + 1
            case 6: 
                return index + 1
            case 7: return index

        return index

    def createPlot(self, plot_name, ax, cols):
        plotInfo = self.plotInfos[plot_name]
        #self.dataPlotter.plot(ax, plotInfo["x"], plotInfo["y"][0], plotInfo.get("scatter", False))
        if len(plotInfo["y"])>1:
            self.dataPlotter.plotDual(ax, plotInfo["x"], *plotInfo["y"], plotInfo.get("scatter", False), self.show_major_background_lines.get(), self.show_minor_background_lines.get(), cols, plotInfo.get("sameAxisScaling", False))
        else:
            self.dataPlotter.plot(ax, plotInfo["x"], plotInfo["y"][0], plotInfo.get("scatter", False), self.show_major_background_lines.get(), self.show_minor_background_lines.get(), cols)

    def on_close(self):
        plt.close("all")
        self.root.quit()
        self.root.destroy()

    def choose_line_color(self):
        color = askcolor()[1]  # returns "#rrggbb" or None if cancelled
        if color is not None:
            self.line_color = color
            self.color_button.configure(bg=self.line_color)

    
    #def maximize(self):
    #    try:
    #        self.root.state("zoomed")          # Windows
    #    except:
    #        self.root.attributes("-zoomed", True)   # Linux fallback

# snapshot functionality ------------------------------

    def refresh_snapshot_ui(self):
        # Clear old rows
        for widget in self.snapshot_container.winfo_children():
            widget.destroy()

        # Ensure container is visible and packed in the correct position
        # Only pack it if it’s not already packed
        if not self.snapshot_container.winfo_ismapped():
            self.snapshot_container.pack(fill=tk.X, padx=10, pady=(0, 5))  # keeps it above the export button

        if not self.snapshots:
            # Hide container if empty
            self.snapshot_container.pack_forget()
            return

        for name in self.snapshots.keys():
            row = tk.Frame(self.snapshot_container, bg="#dde3ec")
            row.pack(fill=tk.X, pady=2)

            # reuse variable if exists
            var = self.snapshot_vars.get(name, tk.BooleanVar(value=False))
            self.snapshot_vars[name] = var

            has_notes = bool(self.snapshots[name]["ui"].get("notes", "").strip())
            label_text = f"{name} 📝" if has_notes else name

            tk.Checkbutton(row, variable=var, bg="#dde3ec").pack(side=tk.LEFT)
            tk.Label(row, text=label_text, bg="#dde3ec").pack(side=tk.LEFT, padx=5)
            tk.Button(row, text="📂", command=lambda n=name: self.load_snapshot(n)).pack(side=tk.LEFT)
            tk.Button(row, text="⋯", command=lambda n=name: self.snapshot_options(n)).pack(side=tk.LEFT)


    def snapshot_options(self, name):
        """Open a popup for rename, reposition, delete"""
        popup = tk.Toplevel(self.root)
        popup.title(f"Options — {name}")
        popup.grab_set()  # modal

        tk.Label(popup, text="Snapshot Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        name_var = tk.StringVar(value=name)
        name_entry = tk.Entry(popup, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(popup, text="Position:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        position_var = tk.StringVar(value=str(list(self.snapshots.keys()).index(name) + 1))
        position_entry = tk.Entry(popup, textvariable=position_var, width=5)
        position_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        def apply_changes():
            current_name = name  # keep original name from outer scope
            new_name = name_var.get().strip()
            pos_text = position_var.get().strip()

            if not new_name:
                tk.messagebox.showerror("Error", "Name cannot be empty", parent=popup)
                return

            if new_name != current_name and new_name in self.snapshots:
                tk.messagebox.showerror("Error", "Name already exists", parent=popup)
                return

            # Validate position
            try:
                new_pos = int(pos_text)
            except ValueError:
                tk.messagebox.showerror("Error", "Position must be an integer", parent=popup)
                return

            keys = list(self.snapshots.keys())
            if new_pos < 1 or new_pos > len(keys):
                tk.messagebox.showerror("Error", f"Position must be between 1 and {len(keys)}", parent=popup)
                return

            # Rename
            if new_name != current_name:
                self.snapshots[new_name] = self.snapshots.pop(current_name)
                if current_name in self.snapshot_vars:
                    self.snapshot_vars[new_name] = self.snapshot_vars.pop(current_name)
                current_name = new_name  # update reference for later

            # Move position
            keys = list(self.snapshots.keys())
            keys.remove(current_name)
            keys.insert(new_pos - 1, current_name)
            self.snapshots = {k: self.snapshots[k] for k in keys}
            self.snapshot_vars = {k: self.snapshot_vars[k] for k in keys}

            self.refresh_snapshot_ui()
            popup.destroy()

        tk.Button(popup, text="Apply", command=apply_changes).grid(row=2, column=0, columnspan=2, pady=10)

        # Delete button
        def delete_snapshot_popup():
            if tk.messagebox.askyesno("Confirm", f"Delete snapshot '{name}'?"):
                self.delete_snapshot(name)
                popup.destroy()

        tk.Button(popup, text="Delete", fg="red", command=delete_snapshot_popup).grid(row=3, column=0, columnspan=2, pady=5)

        popup.columnconfigure(1, weight=1)


    def get_current_state(self):

        def to_serializable(arr):
            import numpy as np
            if isinstance(arr, np.ndarray):
                return arr.tolist()
            if isinstance(arr, list):
                return [to_serializable(x) for x in arr]
            if isinstance(arr, np.generic):
                return arr.item()
            return arr
        
        copy_of_old_interactive_lines_dict= {}
        
        #copy.deepcopy(self.old_interactive_lines_dict)

        for plot_name, lines in self.old_interactive_lines_dict.items():
            for line_id, line in lines.items():
                copy_of_old_interactive_lines_dict.setdefault(plot_name, {})[line_id] = {
                    "x": to_serializable(line["x"]),
                    "y": to_serializable(line["y"]),
                    #"x": line["x"].tolist() if isinstance(line["x"], np.ndarray) else line["x"],
                    #"y": line["y"].tolist() if isinstance(line["y"], np.ndarray) else line["y"],
                    "color": line["color"],
                    "plotInfo": {
                        "x": line["plotInfo"]["x"],
                        "y": line["plotInfo"]["y"],
                        "scatter": line["plotInfo"].get("scatter", False),
                        "angleBisector": line["plotInfo"].get("angleBisector", False),
                    },
                    "id": line["id"]
            }

        #pprint(copy_of_old_interactive_lines_dict)


        for line in self.interactive_lines:
            if line.line is not None:
                xdata, ydata = line.line.get_data()
                copy_of_old_interactive_lines_dict.setdefault(line.plotName, {})[line.id] = {
                    "x": to_serializable(xdata),
                    "y": to_serializable(ydata),
                    #"x": line["x"].tolist() if isinstance(line["x"], np.ndarray) else line["x"],
                    #"y": line["y"].tolist() if isinstance(line["y"], np.ndarray) else line["y"],
                    "color": line.color,
                    "plotInfo": {
                        "x": line.plotInfo["x"],
                        "y": line.plotInfo["y"],
                        "scatter": line.plotInfo.get("scatter", False),
                        "angleBisector": line.plotInfo.get("angleBisector", False),
                    },
                    "id": line.id
                }

        #print("--------------------------")
        #pprint(copy_of_old_interactive_lines_dict)

        #print("###############################")
        return {
            "ui": {
                # --- plot selection ---
                "plot_check_vars": {k: v.get() for k, v in self.plot_check_vars.items()},

                # --- display ---
                "show_major_background_lines": self.show_major_background_lines.get(),
                "show_minor_background_lines": self.show_minor_background_lines.get(),
                "fixed_ratio": self.fixed_ratio.get(),
                "ratio": self.ratio_var.get(),

                # --- labels ---
                "use_smoothed_yValues_for_labels": self.use_smoothed_yValues_for_labels.get(),
                "showParameterNamesForLabels": self.showParameterNamesForLabels.get(),
                "showTimeParamsInTimeFormat": self.showTimeParamsInTimeFormat.get(),

                # --- thresholds ---
                "vt": self.show_ventilatory_thresholds.get(),
                "vt_val": self.show_values_for_ventilatory_thresholds.get(),

                # --- zones ---
                "zones": self.show_training_zones.get(),
                "zone_val": self.show_values_for_training_zones.get(),
                "zone_shading": self.show_shading_for_training_zones.get(),
                "num_zones": self.num_of_zones.get(),
                "transparency": self.transparency_var.get(),

                # --- additional lines ---
                "additional": self.show_additional_lines.get(),
                "line_color": self.line_color,

                # --- parameter calculation ---
                "calculate_parameter": self.calculate_parameter_by_protocol.get(),

                # --- form entries ---
                "entries": {k: v.get() for k, v in self.entry_vars.items()},

                # --- notes
                "notes": self.notes_text.get("1.0", "end-1c"),
            },

            # --- line state ---
            "old_interactive_lines": copy.deepcopy(copy_of_old_interactive_lines_dict),

            # --- shared draggable vertical lines ---
            "shared_x": self.shared_x.copy(), 
            "bisecting_lines_X_dict": copy.deepcopy(self.bisectingLinesXDict)
        }



    def apply_state(self, state):
        ui = state["ui"]

        # --- plot selection ---
        for k, v in ui["plot_check_vars"].items():
            if k in self.plot_check_vars:
                self.plot_check_vars[k].set(v)

        # --- display ---
        self.show_major_background_lines.set(ui["show_major_background_lines"])
        self.show_minor_background_lines.set(ui["show_minor_background_lines"])
        self.fixed_ratio.set(ui["fixed_ratio"])
        self.ratio_var.set(ui["ratio"])

        # --- labels ---
        self.use_smoothed_yValues_for_labels.set(ui["use_smoothed_yValues_for_labels"])
        self.showParameterNamesForLabels.set(ui["showParameterNamesForLabels"])
        self.showTimeParamsInTimeFormat.set(ui["showTimeParamsInTimeFormat"])

        # --- thresholds ---
        self.show_ventilatory_thresholds.set(ui["vt"])
        self.show_values_for_ventilatory_thresholds.set(ui["vt_val"])

        # --- zones ---
        self.show_training_zones.set(ui["zones"])
        self.show_values_for_training_zones.set(ui["zone_val"])
        self.show_shading_for_training_zones.set(ui["zone_shading"])
        self.num_of_zones.set(ui["num_zones"])
        self.transparency_var.set(ui["transparency"])

        # --- additional ---
        self.show_additional_lines.set(ui["additional"])
        self.line_color = ui["line_color"]
        self.color_button.configure(bg=self.line_color)

        # --- parameter ---
        self.calculate_parameter_by_protocol.set(ui["calculate_parameter"])

        # --- entries ---
        for k, v in ui["entries"].items():
            if k in self.entry_vars:
                self.entry_vars[k].set(v)

        # --- notes ---
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", ui.get("notes", ""))

        self.auto_resize_text()

        # --- lines ---
        self.old_interactive_lines_dict = copy.deepcopy(state["old_interactive_lines"])

        # --- shared vertical lines ---
        self.shared_x = state["shared_x"].copy()

        self.bisectingLinesXDict = copy.deepcopy(state["bisecting_lines_X_dict"])

        # update UI-dependent states
        self.on_ratio_toggle(updatePlots=False)

        # redraw once
        self.update_plots(captureLineState = False)




    def save_snapshot(self):
        base = "Snapshot"
        i = 1
        while f"{base} {i}" in self.snapshots:
            i += 1

        name = simpledialog.askstring("Snapshot name", "Enter name:", initialvalue=f"{base} {i}")
        if not name:
            return

        self.snapshots[name] = self.get_current_state()
        self.refresh_snapshot_ui()


    def load_snapshot(self, name):
        self.apply_state(self.snapshots[name])


    def delete_snapshot(self, name):
        del self.snapshots[name]

        if name in self.snapshot_vars:
            del self.snapshot_vars[name]

        self.refresh_snapshot_ui()


    def rename_snapshot(self, name):
        new_name = simpledialog.askstring("Rename", "New name:", initialvalue=name)
        if not new_name or new_name in self.snapshots:
            return

        # Create a new OrderedDict preserving order
        new_snapshots = OrderedDict()
        for k, v in self.snapshots.items():
            if k == name:
                new_snapshots[new_name] = v
            else:
                new_snapshots[k] = v
        self.snapshots = new_snapshots

        # Move checkbox state
        if name in self.snapshot_vars:
            self.snapshot_vars[new_name] = self.snapshot_vars.pop(name)

        self.refresh_snapshot_ui()

    def move_snapshot_up(self, name):
        keys = list(self.snapshots.keys())
        idx = keys.index(name)
        if idx == 0:
            return  # already at top

        # Swap in the keys list
        keys[idx], keys[idx - 1] = keys[idx - 1], keys[idx]

        # Rebuild OrderedDict preserving the swapped order
        self.snapshots = OrderedDict((k, self.snapshots[k]) for k in keys)

        # Also move the checkbox states
        self.snapshot_vars = OrderedDict((k, self.snapshot_vars[k]) for k in keys)

        self.refresh_snapshot_ui()


    def move_snapshot_down(self, name):
        keys = list(self.snapshots.keys())
        idx = keys.index(name)
        if idx == len(keys) - 1:
            return  # already at bottom

        # Swap in the keys list
        keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]

        # Rebuild OrderedDict preserving the swapped order
        self.snapshots = OrderedDict((k, self.snapshots[k]) for k in keys)

        # Also move the checkbox states
        self.snapshot_vars = OrderedDict((k, self.snapshot_vars[k]) for k in keys)

        self.refresh_snapshot_ui()



    def save_to_file(self):
        #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".spiro",
            filetypes=[("Spiro files", "*.spiro")],
            initialfile = f"{self.suggestedFileName}.spiro",
            initialdir=self.file_dir_path
        )
        if not file_path:
            return

        self.suggestedFileName = os.path.splitext(os.path.basename(file_path))[0]
        self.file_dir_path = os.path.dirname(file_path)

        data = {
            "current_state": self.get_current_state(),
            "snapshots": copy.deepcopy(self.snapshots),
            "xmlFile": self.xmlFile,
            "meta": {
                "version": 1.0
            }
        }

        def convert(obj):
            """Helper to make numpy + UUID JSON serializable"""
            import numpy as np
            import uuid

            if isinstance(obj, np.generic):
                return obj.item()
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return obj

        try:
            # Create zip archive
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:

                # -------------------------
                # 1. Add XML file
                # -------------------------
                if not os.path.exists(self.xmlFile):
                    logging.error(f"XML file not found: {self.xmlFile}")
                    tk.messagebox.showerror("Error", "Original XML file not found!")
                    return

                xml_filename = os.path.basename(self.xmlFile)
                zf.write(self.xmlFile, arcname=xml_filename)

                # -------------------------
                # 2. Add spiroHuskyApplicationState.json
                # -------------------------
                settings_json = json.dumps(data, indent=2, default=convert)

                zf.writestr("spiroHuskyApplicationState.json", settings_json)

            logging.info(f"Saved .spiro archive → {file_path}")

        except Exception as e:
            logging.error(f"Failed to save .spiro file: {e}")
            tk.messagebox.showerror("Error", f"Failed to save file:\n{e}")


    def export_pdf(self):
        # --- get selected snapshots ---
        selected_snapshots = [
            name for name, var in self.snapshot_vars.items() if var.get()
        ]

        if not selected_snapshots:
            self.show_temporary_alert(self.root, "No snapshots selected")
            logging.info("No snapshots selected.")
            return

        #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile = f"{self.suggestedFileName}.pdf",
            initialdir=self.file_dir_path
        )
        if not file_path:
            return

        self.file_dir_path = os.path.dirname(file_path)

        # --- backup current state ---
        current_state_backup = self.get_current_state()

        with PdfPages(file_path) as pdf:
            for name in selected_snapshots:
                logging.info(f"Exporting snapshot: {name}")

                # --- apply snapshot (this redraws plots exactly like UI) ---
                self.apply_state(self.snapshots[name])

                # --- force UI update (important for Tkinter) ---
                self.root.update_idletasks()
                self.root.update()

                # --- grab all current figures ---
                figs = [plt.figure(num) for num in plt.get_fignums()]

                for fig in figs:
                    pdf.savefig(fig)

        # --- restore previous state ---
        self.apply_state(current_state_backup)

        logging.info(f"Exported PDF → {file_path}")


    def export_pngs(self):
        # --- get selected snapshots ---
        selected_snapshots = [
            name for name, var in self.snapshot_vars.items() if var.get()
        ]

        if not selected_snapshots:
            self.show_temporary_alert(self.root, "No snapshots selected")
            logging.info("No snapshots selected.")
            return

        # --- select base directory ---
        base_dir = filedialog.askdirectory(
            title="Select base directory", 
            initialdir=self.file_dir_path)
        if not base_dir:
            return

        self.file_dir_path = base_dir

        # --- create unique folder ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{self.suggestedFileName}_{timestamp}"
        export_dir = os.path.join(base_dir, folder_name)

        counter = 1
        while os.path.exists(export_dir):
            export_dir = os.path.join(base_dir, f"{folder_name}_{counter}")
            counter += 1

        os.makedirs(export_dir)

        logging.info(f"Exporting PNGs to: {export_dir}")

        # --- backup current state ---
        current_state_backup = self.get_current_state()

        for name in selected_snapshots:
            logging.info(f"Exporting snapshot: {name}")

            # --- apply snapshot ---
            self.apply_state(self.snapshots[name])

            # --- force UI update ---
            self.root.update_idletasks()
            self.root.update()

            # --- get all figures ---
            figs = [plt.figure(num) for num in plt.get_fignums()]

            for i, fig in enumerate(figs):
                safe_name = name.replace(" ", "_").replace("/", "_")

                filename = f"{safe_name}"
                if len(figs) > 1:
                    filename += f"_fig{i+1}"

                filepath = os.path.join(export_dir, f"{filename}.png")

                fig.savefig(filepath, dpi=300)
                logging.info(f"Saved → {filepath}")

        # --- restore previous state ---
        self.apply_state(current_state_backup)

        logging.info("PNG export complete.")

    def auto_resize_text(self, event=None):
        text_widget = self.notes_text

        # Count number of lines
        num_lines = int(text_widget.index('end-1c').split('.')[0])

        # Optional: clamp size
        min_lines = 3
        max_lines = 15

        new_height = max(min_lines, min(max_lines, num_lines))

        text_widget.config(height=new_height)


    def show_temporary_alert(self, root, message, duration=1500):
        """
        Show a larger temporary alert message that disappears after `duration` milliseconds.
        """
        # Create a top-level window
        alert = tk.Toplevel(root)
        alert.overrideredirect(True)  # remove window decorations
        alert.attributes("-topmost", True)  # keep on top
        alert.configure(bg="#f8d7da")  # light red background for warning

        # Message label
        label = tk.Label(
            alert,
            text=message,
            bg="#f8d7da",
            fg="#b91818",
            font=("Segoe UI", 14, "bold"),  # increased font size
            padx=20,  # more horizontal padding
            pady=10   # more vertical padding
        )
        label.pack()

        # Force a minimum width for visibility
        min_width = 300
        alert.update_idletasks()
        width = max(alert.winfo_reqwidth(), min_width)
        height = alert.winfo_reqheight()

        # Position alert in the center of main window
        x = root.winfo_rootx() + root.winfo_width() // 2 - width // 2
        y = root.winfo_rooty() + root.winfo_height() // 2 - height // 2
        alert.geometry(f"{width}x{height}+{x}+{y}")

        # Auto-destroy after duration
        alert.after(duration, alert.destroy)


    def load_from_file_content(self, spiroFileContent):
        """
        Load the GUI state from a previously saved .spiro file content.
        spiroFileContent: dict loaded from JSON, containing 'current_state', 'snapshots', and 'xmlFile'
        """
        logging.info(f"Loading session from Spiro file (XML: {spiroFileContent.get('xmlFile')})")

        # Load snapshots
        self.snapshots = spiroFileContent.get("snapshots", OrderedDict())
        # Recreate snapshot UI variables
        self.snapshot_vars = {name: tk.BooleanVar(value=False) for name in self.snapshots.keys()}

        # Apply the main saved state
        if "current_state" in spiroFileContent:
            self.apply_state(spiroFileContent["current_state"])
        else:
            logging.warning("Spiro file content has no 'current_state'; nothing applied.")

        # Refresh snapshot UI
        self.refresh_snapshot_ui()
        logging.info("Spiro file loaded successfully.")