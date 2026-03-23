from ymlReader import YmlReader
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import numpy as np
import matplotlib.ticker as mticker
import math
from dataConversion import DataConversion
from itertools import chain
import logging
import os

class DataExtraction:
  def __init__(self, xmlFile, basePath, file_dir_path):

    configInFileDir = os.path.join(file_dir_path, "spiroHuskyConfig.yml")

    if os.path.exists(configInFileDir):
      logging.info(f"Found config file in same directory as data file: {configInFileDir}")
      self.ymlReader = YmlReader(configInFileDir)
    elif os.path.exists(os.path.join(basePath, "spiroHuskyConfig.yml")):
      logging.info(f"Found config file in application directory: {os.path.join(basePath, 'spiroHuskyConfig.yml')}")
      self.ymlReader = YmlReader(os.path.join(basePath, "spiroHuskyConfig.yml"))
    else:
      logging.error("No config file found. Please make sure spiroHuskyConfig.yml is located either in the application directory or in the same directory as the data file.")
      raise FileNotFoundError("No config file found. Please make sure spiroHuskyConfig.yml is located either in the application directory or in the same directory as the data file.")

    self.config = self.ymlReader.read()

    self.tree = ET.parse(xmlFile)
    self.root = self.tree.getroot()
    self.NS = {
        "ss": "urn:schemas-microsoft-com:office:spreadsheet"
    }
    self.worksheet = self.root.find(".//ss:Worksheet", self.NS)
    self.table = self.worksheet.find(".//ss:Table", self.NS)
    self.rows = self.table.findall("ss:Row", self.NS)

  def extractData(self):
    headerRows = []
    headerIndices = []
    for i, row in enumerate(self.rows):
        for cell in row.findall("ss:Cell", self.NS):
            #style = cell.get(f"{{{self.NS['ss']}}}StyleID")
            contentLower = (cell.find("ss:Data", self.NS).text or "").lower()
            if any(keyword.lower() in contentLower for keyword in self.config["headerRecognitionKeywords"]):
                headerRows.append(row)
                headerIndices.append(i)
                break

    self.dataRows = self.rows[headerIndices[-1]+1:]

    self.colToParam = {idx:param for idx, param in enumerate(cell.find("ss:Data", self.NS).text for cell in headerRows[-2].findall("ss:Cell", self.NS))}
    self.paramToCol = {param:idx for idx, param in self.colToParam.items()}

    self.colToUnit = {idx:param for idx, param in enumerate(cell.find("ss:Data", self.NS).text for cell in headerRows[-1].findall("ss:Cell", self.NS))}
    self.paramToUnit = {param: self.colToUnit[col] for col, param in self.colToParam.items()}
    self.paramToDigitsAfterComma = {
        param["name"]: param.get("digitsAfterComma", 2)
        for param in chain(
            self.config.get("readParams", []),
            self.config.get("calculatedParams", [])
        )
    }
    self.dataDictionary = {}
    for param in self.config["readParams"]:
       if param["name"] in self.paramToCol:
        selectedCol = self.selectCol(param["name"])
        if any(not math.isnan(x) for x in selectedCol):
          self.dataDictionary.update({param["name"]: selectedCol})

    for calcParam in self.config["calculatedParams"]:
      required_keys = ["name", "usedParam1", "operation"]
      # Skip the loop if any required key is missing or empty
      if any(not calcParam.get(k) for k in required_keys):
        logging.warning(f"Calculated parameter was missing a required element: {calcParam}")
        continue

      match calcParam["operation"]:
        case "div":
          if not calcParam.get("usedParam2"):
            logging.warning(f"Calculated parameter '{calcParam.name}' was missing a required element: usedParam2")
            continue
          if calcParam["usedParam1"] in self.dataDictionary and calcParam["usedParam2"] in self.dataDictionary:
            self.dataDictionary.update({calcParam["name"]: [p1 / p2 for p1, p2 in zip(self.dataDictionary[calcParam["usedParam1"]], self.dataDictionary[calcParam["usedParam2"]])]})
          else:
            logging.warning(f"Used parameters for calculated parameter {calcParam["name"]} not found.")
        case "smoothMonotonic":
          if calcParam["usedParam1"] in self.dataDictionary:
            self.dataDictionary.update({calcParam["name"]: DataConversion.smoothMonotonic(self.dataDictionary[calcParam["usedParam1"]])})
          else:
            logging.warning(f"Used parameters for calculated parameter {calcParam["name"]} not found.")
        case _:
          logging.warning(f"Operation {calcParam["operation"]} is not supported. Please check config for param {calcParam["name"]}.")


  def isFloat(self, value):
    try:
      float(value)
      return True
    except (ValueError, TypeError):
      return False

  def selectCol(self, param):
    isTimeValue = False
    colItems = []
    idx = self.paramToCol[param]
    for row in self.dataRows:
      rawValue = row.findall("ss:Cell", self.NS)[idx].find("ss:Data", self.NS).text
      if self.isFloat(rawValue):
        colItems.append(float(rawValue))
      else:
        try:
          t = datetime.strptime(rawValue, "%H:%M:%S,%f")
          seconds = t.hour*3600 + t.minute*60 + t.second + t.microsecond/1_000_000
          minutes = seconds/60.0
          colItems.append(minutes)
          isTimeValue = True
        except ValueError:
          # fallback if neither float nor datetime
          colItems.append(np.nan)
          logging.warning(f"could not read value {rawValue} for param {param}.")
    
    if isTimeValue:
      self.paramToUnit[param] = "min"
      self.colToUnit[idx] = "min"

    return colItems




