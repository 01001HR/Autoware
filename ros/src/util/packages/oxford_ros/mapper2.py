#!/usr/bin/python


import sys
import sdk
from tf import transformations as trafo
import numpy as np
import bisect


def interpolatePose (targetTimestamp, lidarTimestamps, poses):
    u_1 = bisect.bisect_left(lidarTimestamps, targetTimestamp)
    u_2 = bisect.bisect_right(lidarTimestamps, targetTimestamp)
    fraction = (targetTimestamp - lidarTimestamps[u_1]) / \
        (lidarTimestamps[u_2] - lidarTimestamps[u_1])
    p1 = poses[u_1]
    p2 = poses[u_2]
    movement = p2[0:3] - p1[0:3]
    translation = p1[0:3] + fraction*movement
    rotation = trafo.quaternion_slerp(p1[3:4], p1[3:4], fraction)
    return np.array([translation[0], translation[1], translation[2],
        rotation[0], rotation[1], rotation[2], rotation[3]])
    

def readScan (path):
    scanMat = np.fromfile(path, np.double).reshape ((len(scan) // 3,3)).astype(np.float32)
    scanz = np.zeros((scan.shape[0], 4), dtype=scan.dtype)
    scanz[:,0:2] = scanMat[:,0:2]
    # X Axis from scans is negated to comform with right-hand convention
    scanz[:,0] = -scanz[:,0]
    scanz[:,3] = 1
    return scanz


def buildMap(datasetDir):
    dataset = sdk.Dataset (datasetDir)
    scanList = []
    
    posesTbl = dataset.getIns ()
    poses = np.zeros((len(posesTbl), 7))
    for i in range(len(poses)):
        r = posesTbl[i]
        poses[i, 0:3] = posesTbl[i, r[1:3]]
        poses[i, 3:4] = trafo.quaternion_from_euler(r[4], r[5], r[6]) 
    
    lidarFileList = dataset.getLidar2D ()
    lidarTimestamps = [l['timestamp'] for l in lidarFileList]
    
    for fip in range(len(lidarFileList)) :
        scan = readScan(lidarFileList[fip])
        pass


if __name__ == '__init__' :
    pass