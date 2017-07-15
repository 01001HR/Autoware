#!/usr/bin/python

import sys
import rosbag

import sdk
from player import ImagePlayer, PosePlayer, Lidar2Player, Lidar3Player


def DatasetToRosbag (datasetDir, bagOutputPath):
    dataset = sdk.Dataset (datasetDir)
    bagOutput = rosbag.Bag(bagOutputPath, mode='w')
    
    images = ImagePlayer (dataset)
    poses = PosePlayer (dataset)
    lidar2 = Lidar2Player (dataset)
    lidar3 = Lidar3Player (dataset) 
    for player in [images, poses, lidar2, lidar3] :
        events = player._getEvents ()
        for evt in events :
            msg = player._passEvent (evt['timestamp'], evt['id'], publish=False)
            
            
    bagOutput.close()
    


if __name__ == '__main__' :
    pass