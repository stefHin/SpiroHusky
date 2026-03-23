from dataExtraction import DataExtraction
from dataPlotter import DataPlotter
from PlotGUI import PlotGUI
from datetime import datetime, timedelta
import numpy as np
import matplotlib.ticker as mticker
import math
import tkinter as tk
from tkinter import ttk
from dataConversion import DataConversion
import logging
import sys
from datetime import datetime
import os
from logging.handlers import RotatingFileHandler
import sys
from tkinter import filedialog
import ctypes
import zipfile
import tempfile
import shutil
import atexit
import tkinter.messagebox as messagebox


def createPlotInfoDict(dataDictionary, potentialPlot):
  plotInfos = {}
  for plotInfo in potentialPlot:
    if not plotInfo["x"] in dataDictionary:
      logging.warning(f"param x not found in data: {plotInfo['x']}")
      continue

    if any(not y in dataDictionary for y in plotInfo["y"]):
      logging.warning(f"param y not found in data: {plotInfo['y']}")
      continue
    
    if len(plotInfo["y"])>1:
      name = ", ".join(plotInfo["y"]) + f" vs {plotInfo['x']}"
    else:
      name = f"{plotInfo['y'][0]} vs {plotInfo['x']}"

    plotInfos.update({name: plotInfo})

  return plotInfos


def setup_logging(root=None):
    """
    Sets up a rotating log file for the entire application.
    root: optional Tk instance for automatic Tkinter callback logging
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "spiroHusky.log")

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        mode="a",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8"
    )

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    # Catch uncaught exceptions globally (main thread)
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    # Catch Tkinter callback exceptions
    if root is not None:
        root.report_callback_exception = lambda et, ev, tb: logging.critical(
            "Uncaught exception in Tkinter callback",
            exc_info=(et, ev, tb)
        )

def get_input_file():
    if len(sys.argv) > 1:
        return sys.argv[1]  # file passed via "Open With"
    else:
        root = tk.Tk()
        root.withdraw()  # hide root window
        file_path = filedialog.askopenfilename(
            title="Select CPET XML or Spiro file",
            filetypes = [
                ("Supported files", "*.xml *.spiro"),
                ("CPET XML files", "*.xml"),
                ("Spiro files", "*.spiro"),
            ],
            initialdir=exe_dir_path
        )
        root.destroy()
        return file_path

def cleanup_temp_dir():
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Cleaned up temp dir: {temp_dir}")
    except Exception as e:
        logging.warning(f"Failed to clean temp dir: {e}")


temp_dir = None

if getattr(sys, 'frozen', False):
    # Running as PyInstaller exe
    exe_dir_path = os.path.join(os.path.dirname(sys.executable))
else:
    # Running as script
    exe_dir_path = os.path.dirname(os.path.abspath(__file__))

log_dir = os.path.join(exe_dir_path, "logs")

setup_logging()
logging.info("=== Application started ===")

atexit.register(cleanup_temp_dir)

input_file = get_input_file()
if not input_file:
    logging.info("No file selected. Exiting...")
    sys.exit(0)

# ---------------- Load Data ----------------
file_ext = os.path.splitext(input_file)[1].lower()
file_dir_path = os.path.dirname(input_file)

if file_ext == ".xml":
    logging.info(f"Selected XML file: {input_file}")
    xmlFile = input_file
    spiroFileContent = None
    spiroFileName = None
elif file_ext == ".spiro":
    logging.info(f"Loading Spiro archive: {input_file}")
    spiroFileName = os.path.basename(input_file)

    import json

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="spiro_")
    logging.info(f"Extracting spiro archive to temp dir: {temp_dir}")

    try:
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find required files
        xmlFile = None
        applicationStatePath = None

        for root_dir, _, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith(".xml"):
                    xmlFile = os.path.join(root_dir, file)
                elif file.lower() == "spirohuskyapplicationstate.json":
                    applicationStatePath = os.path.join(root_dir, file)

        if not xmlFile:
            logging.error("No XML file found inside .spiro archive!")
            sys.exit(1)

        if applicationStatePath:
            with open(applicationStatePath, "r", encoding="utf-8") as f:
                spiroFileContent = json.load(f)
        else:
            logging.warning("No spiroHuskyApplicationState.json found inside archive.")
            spiroFileContent = None

    except zipfile.BadZipFile:
        logging.error("Invalid .spiro file (not a valid zip archive)")
        sys.exit(1)
else:
    logging.error(f"Unsupported file type: {file_ext}")
    sys.exit(1)

try:
    dataExtraction = DataExtraction(xmlFile, exe_dir_path, file_dir_path)
    dataExtraction.extractData()
except FileNotFoundError as e:
    logging.error(str(e))
    messagebox.showerror("Missing Configuration", str(e))
    sys.exit(1)

#dataPlotter = DataPlotter(dataExtraction.dataDictionary)

dataConversion = DataConversion(dataExtraction)

plotInfos = createPlotInfoDict(dataExtraction.dataDictionary, dataExtraction.config["plots"])


if __name__ == "__main__":
    root = tk.Tk()
    root.report_callback_exception = lambda et, ev, tb: logging.critical(
        "Uncaught exception in Tkinter callback",
        exc_info=(et, ev, tb)
    )

    icon_path = os.path.join(exe_dir_path, "spiroHuskyIcon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(default=icon_path)  # <-- 'default=' is important
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"com.yourcompany.spirohusky")
            hicon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
            if hicon:
                ctypes.windll.user32.SendMessageW(root.winfo_id(), 0x80, 0, hicon)
        except Exception as e:
            logging.warning(f"Failed to set icon: {e}")
    else:
        logging.warning(f"Icon file not found at {icon_path}. Using default icon.")

    root.title("SpiroHusky v1.0")

    gui = PlotGUI(root, dataExtraction, plotInfos, dataConversion, xmlFile, file_dir_path, spiroFileContent, spiroFileName)

    #root.after(10, gui.maximize)
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")

    root.deiconify()                  # Ensure window is visible
    root.lift()                        # Raise above other windows
    root.attributes("-topmost", True)
    root.after(100, lambda: root.attributes("-topmost", False))
    root.mainloop()




