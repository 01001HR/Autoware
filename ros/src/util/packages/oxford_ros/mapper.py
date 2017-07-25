#!/usr/bin/python

import pickle
import numpy as np
import rospy
import sys
from sensor_msgs.msg import PointCloud2
from player import Lidar2Player, PosePlayer
import sdk
from tf import transformations as trafo, TransformListener
import sensor_msgs.point_cloud2 as pcl2
from twisted.internet.test.reactormixins import process


tfListen = None
scanList = []
numOfPoints = 0


def laserCallback (msg):
    global numOfPoints
    
    t = msg.header.stamp.to_sec()-0.05
    currentPos, currentRot = tfListen.lookupTransform ('world', Lidar2Player._lidarName, rospy.Time.from_sec(t))

    points = pcl2.read_points(msg)
    cmsg = {
        'timestamp':msg.header.stamp.to_sec(), 
        'pose':(currentPos, currentRot), 
        'scan':np.zeros((msg.width*msg.height, 3), dtype=np.float32)}
    i = 0
    for p in points:
        cmsg['scan'][i] = p[0:3]
        i += 1
    scanList.append (cmsg)
    numOfPoints += (msg.width*msg.height)
    
    
def doBuildMap (scanInput):
    numOfPts = 0
    for s in scanInput:
        numOfPts += s['scan'].shape[0]
    pointCloudMap = np.zeros((numOfPts, 3), dtype=np.float32)
    
    i = 0
    for scanRt in scanInput:
        curPos = trafo.translation_matrix (scanRt['pose'][0])
        curRot = trafo.quaternion_matrix (scanRt['pose'][1])
        poseMat = trafo.concatenate_matrices(curRot, curPos)
        poseMat = np.linalg.inv(poseMat)
        scan = scanRt['scan']
        for point in scan:
            pt = np.array([point[0], point[1], point[2], 1])
            pt = np.dot(poseMat, pt)
            pointCloudMap[i] = pt[0:3]
            i += 1
    return pointCloudMap


def processScans (savePath):
    pickle.dump(scanList, open('/tmp/scandebug.pickle', 'w'))
    
    pointCloudMap = doBuildMap(scanList)
            
    sdk.create_pointcloud_file (pointCloudMap, savePath)


if __name__ == '__main__' :
    
    rospy.init_node ('ox_mapper', anonymous=True)
    rospy.Subscriber (Lidar2Player.topicName, PointCloud2, laserCallback, queue_size=100)
    tfListen = TransformListener()
    
    rospy.spin()
    print ("Done")
    print ("Length: {}".format(len(scanList)))
    print ("# of Points: {}".format(numOfPoints))
    print ("Processing...")
    processScans('/tmp/test.pcd')
    