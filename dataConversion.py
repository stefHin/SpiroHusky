import numpy as np
import logging


class DataConversion:
    def __init__(self, dataExtraction):
        self.dataExtraction = dataExtraction
        self.baseTimeParam = dataExtraction.config["baseTimeParam"]
        self.baseTimeValues = dataExtraction.dataDictionary[self.baseTimeParam]
        self.origParams = dataExtraction.dataDictionary
        self.smoothedParams = {key: self.smooth(valuesList) for key, valuesList in dataExtraction.dataDictionary.items()}
        self.smoothedMonotonicParams = {key: self.smoothMonotonic(valuesList) for key, valuesList in dataExtraction.dataDictionary.items()}

    @staticmethod
    def smooth(values):
        window = 5  # number of points to average
        smoothedValues = np.convolve(values, np.ones(window)/window, mode='same')

        return smoothedValues

    @staticmethod
    def smoothMonotonic(values):
        smoothedValues = DataConversion.smooth(values)

        monotonicValues = np.maximum.accumulate(smoothedValues)

        return monotonicValues

    
    def convertToBaselineParam(self, paramName, value, usedParams="smoothedMonotonic"):
        match usedParams:
            case "orig":
                paramValues = self.origParams[paramName]
            case "smoothed":
                paramValues = self.smoothedParams[paramName]
            case _:
                paramValues = self.smoothedMonotonicParams[paramName]

        for i in range(len(paramValues)):
            if paramValues[i] >= value or i == len(paramValues)-1:
                if i == 0:
                    return self.baseTimeValues[0]
                else:
                    relativePos = ((value - paramValues[i-1]) / (paramValues[i] - paramValues[i-1])) if (paramValues[i] - paramValues[i-1]) != 0 else 0
                    return self.baseTimeValues[i-1] + relativePos * (self.baseTimeValues[i] - self.baseTimeValues[i-1])
            
    def convertFromBaselineParam(self, paramName, value, usedParams="smoothedMonotonic"):
        match usedParams:
            case "orig":
                paramValues = self.origParams[paramName]
            case "smoothed":
                paramValues = self.smoothedParams[paramName]
            case _:
                paramValues = self.smoothedMonotonicParams[paramName]
    
        for i in range(len(self.baseTimeValues)):
            if self.baseTimeValues[i] >= value or i == len(self.baseTimeValues)-1:
                if i == 0:
                    return paramValues[0]
                else:
                    relativePos = ((value - self.baseTimeValues[i-1]) / (self.baseTimeValues[i] - self.baseTimeValues[i-1])) if self.baseTimeValues[i] - self.baseTimeValues[i-1] != 0 else 0
                    return paramValues[i-1] + relativePos * (paramValues[i] - paramValues[i-1])