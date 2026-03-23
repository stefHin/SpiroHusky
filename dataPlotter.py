from datetime import datetime, timedelta
import numpy as np
import matplotlib.ticker as mticker
import math
import matplotlib.pyplot as plt
import logging


class DataPlotter:
  def __init__(self, dataExtraction):
    self.dataExtraction = dataExtraction
    self.dataDictionary = self.dataExtraction.dataDictionary

  def plot(self, ax, xParam, yParam, scatter=False, majorBackgroundLines=True, minorBackgroundLines=True, cols=1):
    #fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    x = self.dataDictionary[xParam]
    y = self.dataDictionary[yParam]

    if scatter:
      ax.scatter(x, y, s=15//cols)
    else:
      ax.plot(x, y)

    unitX = self.dataExtraction.paramToUnit.get(xParam)
    ax.set_xlabel(xParam + (f" [{unitX}]" if unitX is not None else ""))

    unitY = self.dataExtraction.paramToUnit.get(yParam)
    ax.set_ylabel(yParam + (f" [{unitY}]" if unitY is not None else ""))
    #ax.set_title(f"{yParam} vs {xParam}")

    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    
  #  ax.xaxis.set_major_locator(computeStepSize(x)[0])
  #  ax.xaxis.set_minor_locator(computeStepSize(x)[1])
  #  ax.yaxis.set_major_locator(computeStepSize(y)[0])
  #  ax.yaxis.set_minor_locator(computeStepSize(y)[1])

    if majorBackgroundLines:
      ax.grid(which='major', color="#B9B9B9", linestyle='-', linewidth=0.5)

    if minorBackgroundLines:
      ax.grid(which='minor', color="#d1d1d1", linestyle='--', linewidth=0.3)
    
    #plt.show()

  def plotDual(self, ax1, xParam, yParam1, yParam2, scatter=False, majorBackgroundLines=True, minorBackgroundLines=True, cols=1, sameAxisScaling=False):
    x = self.dataDictionary[xParam]
    y1 = self.dataDictionary[yParam1]
    y2 = self.dataDictionary[yParam2]

    #fig, ax1 = plt.subplots(figsize=(12, 8), dpi=300)

    # --- First Y axis (left) ---
    if scatter:
      line1 = ax1.scatter(x, y1, color="tab:blue", s=15//cols)
    else:
      line1, = ax1.plot(x, y1, color="tab:blue")

    unitX = self.dataExtraction.paramToUnit.get(xParam)
    unitY1 = self.dataExtraction.paramToUnit.get(yParam1)
    ax1.set_xlabel(xParam + (f" [{unitX}]" if unitX is not None else ""))
    ax1.set_ylabel(yParam1 + (f" [{unitY1}]" if unitY1 is not None else ""), color="tab:blue")
    ax1.tick_params(axis='y', labelcolor="tab:blue")

  #  ax1.xaxis.set_major_locator(computeStepSize(x)[0])
  #  ax1.xaxis.set_minor_locator(computeStepSize(x)[1])
  #  ax1.yaxis.set_major_locator(computeStepSize(y1)[0])
  #  ax1.yaxis.set_minor_locator(computeStepSize(y1)[1])
    if majorBackgroundLines:
      ax1.grid(which='major', color="#99bfd1", linestyle='-', linewidth=0.5)

    if minorBackgroundLines:
      ax1.grid(which='minor', color="#99cbd1", linestyle='--', linewidth=0.3)

    # --- Second Y axis (right) ---
    ax2 = ax1.twinx()
    ax1.twin = ax2
    ax2.twin = ax1

    if scatter:
      line2 = ax2.scatter(x, y2, color="tab:red", s=15//cols)
    else:
      line2, = ax2.plot(x, y2, color="tab:red")

    unitY2 = self.dataExtraction.paramToUnit.get(yParam2)
    ax2.set_ylabel(yParam2 + (f" [{unitY2}]" if unitY2 is not None else ""), color="tab:red")
    ax2.tick_params(axis='y', labelcolor="tab:red")

    ax1.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax1.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax2.yaxis.set_minor_locator(mticker.AutoMinorLocator())

    if majorBackgroundLines:
      ax2.grid(which='major', color="#d19999", linestyle='-', linewidth=0.5)
    
    if minorBackgroundLines:
      ax2.grid(which='minor', color="#e6b3b3", linestyle='--', linewidth=0.3)

        # --- Apply same Y-axis scaling if requested ---
    if sameAxisScaling:
      combined_min = min(np.min(y1), np.min(y2))
      combined_max = max(np.max(y1), np.max(y2))
      margin = (combined_max - combined_min) * 0.05  # optional 5% margin
      ax1.set_ylim(combined_min - margin, combined_max + margin)
      ax2.set_ylim(combined_min - margin, combined_max + margin)

  #  ax2.yaxis.set_major_locator(computeStepSize(y2)[0])
  #  ax2.yaxis.set_minor_locator(computeStepSize(y2)[1])

    #plt.title(f"{yParam1} & {yParam2} vs {xParam}")
    #plt.show()