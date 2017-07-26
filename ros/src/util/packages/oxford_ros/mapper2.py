#!/usr/bin/python


import sys
import sdk
from tf import transformations as trafo
import numpy as np
import bisect


def interpolatePose (targetTimestamp, lidarTimestamps, poses):
    pass


def buildMap(datasetDir):
    dataset = sdk.Dataset (datasetDir)
    scanList = []
    
    poses = dataset.getIns ()
    lidarFileList = dataset.getLidar2D ()
    lidarTimestamps = [l['timestamp'] for l in lidarFileList]


if __name__ == '__init__' :
    pass