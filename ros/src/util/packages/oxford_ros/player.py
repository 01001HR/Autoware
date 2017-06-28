#!/usr/bin/python

import sdk
import time
import rospy
import yaml
import cv2
import cv_bridge
import rospkg
from tf import transformations
import numpy as np

from geometry_msgs.msg import PoseStamped as PoseMsg
from sensor_msgs.msg import Image as ImageMsg
from rosgraph_msgs.msg import Clock



class ImagePlayer:
    def __init__ (self, dataset):
        self.publisher = rospy.Publisher ('/oxford/image', ImageMsg, queue_size=1)
        self.imageList = dataset.getStereo()
        pkgpack = rospkg.RosPack()
        path = pkgpack.get_path('oxford_ros')
#         self.cameraModel = sdk.CameraModel (path+'/models', sdk.CameraModel.cam_stereo_center)
        
        calib_file = file(path+'/calibration_files/bb_xb3_center.yaml')
        conf = yaml.load(calib_file)
        self.camera_matrix = np.reshape(conf['camera_matrix']['data'], (3,3))
        self.projection_matrix = np.reshape(conf['projection_matrix']['data'], (3,4))
        self.distortion_coefs = np.array(conf['distortion_coefficients']['data'])
#         self.calibrator = cv2.cv.Load(path+'/calibration_files/bb_xb3_center.yaml')
        self.cvbridge = cv_bridge.CvBridge()

    def _getEvents (self):
        eventList = [ {'timestamp':self.imageList[i]['timestamp'], 'id':i} for i in range(len(self.imageList)) ]
        return eventList
    
    def _passEvent (self, timestamp, eventId, publish=True):
        imageTarget = self.imageList[eventId]
        image_ctr = cv2.imread(imageTarget['center'], cv2.IMREAD_ANYCOLOR)
        image_ctr = cv2.cvtColor(image_ctr, cv2.COLOR_BAYER_GR2BGR)
        # Using camera matrix
        image_ctr = cv2.undistort(image_ctr, self.camera_matrix, self.distortion_coefs)
        # Using LUT
#         image_ctr = self.cameraModel.undistort (image_ctr)
        msg = self.cvbridge.cv2_to_imgmsg(image_ctr, 'bgr8')
        msg.header.stamp = rospy.Time.from_sec (imageTarget['timestamp'])
        if (publish):
            self.publisher.publish(msg)
        else:
            return msg


class PosePlayer:
    def __init__ (self, dataset):
        self.poses = dataset.getIns()
        self.publisher = rospy.Publisher ('/oxford/pose', PoseMsg, queue_size=1)
    
    def _getEvents (self):
        eventList = [{'timestamp':self.poses[p,0], 'id':p} for p in range(len(self.poses))]
        return eventList
    
    def _passEvent (self, timestamp, eventId, publish=True):
        poseRow = self.poses[eventId]
        curPose = PosePlayer.createPoseFromRPY(poseRow[1], poseRow[2], poseRow[3], poseRow[4], poseRow[5], poseRow[6])
        curPose.header.stamp = rospy.Time.from_sec(poseRow[0])
        curPose.header.frame_id = 'world'
        if (publish):
            self.publisher.publish(curPose)
        else:
            return curPose
        
    @staticmethod
    def createPoseFromRPY (x, y, z, roll, pitch, yaw):
        p = PoseMsg()
        p.pose.position.x = x
        p.pose.position.y = y
        p.pose.position.z = z
        qt = transformations.quaternion_from_euler(roll, pitch, yaw)
        p.pose.orientation.x = qt[0]
        p.pose.orientation.y = qt[1]
        p.pose.orientation.z = qt[2]
        p.pose.orientation.w = qt[3]
        return p


class Player:
    def __init__ (self, datadir, rate=1.0):
        self.rate = float(rate)
        self.eventList = []
        self.dataset = sdk.Dataset(datadir)
        self.players = []
#         self.clockPub = rospy.Publisher ('/clock', Clock, queue_size=1)
        
    def add_data_player (self, _dataPlayer):
        self.players.append(_dataPlayer)
    
    def run (self):
        self.initRun()
        try:
            for i in range(len(self.eventList)):
                curEvent = self.eventList[i]
                t1 = curEvent['timestamp']
                curEvent['object']._passEvent (curEvent['timestamp'], curEvent['id'])
                if i<len(self.eventList)-1 :
                    t2 = self.eventList[i+1]['timestamp']
                    delay = (t2 - t1) / self.rate
#                     self.publishClock(curEvent['timestamp'])
                    time.sleep(delay)
                if (rospy.is_shutdown()):
                    break
        except KeyboardInterrupt:
            print ("Interrupted")
            return
        
    def publishClock (self, t):
        ct = Clock()
        ct.clock = rospy.Time.from_sec(t)
        self.clockPub.publish(ct)
    
    def initRun (self):
        for player in self.players:
            eventsInThis = player._getEvents ()
            if len(eventsInThis)==0:
                continue
            for evt in eventsInThis:
                e = {'timestamp': evt['timestamp'], 'id':evt['id'], 'object':player}
                self.eventList.append(e)
        self.eventList.sort(key=lambda e: e['timestamp'])
        
        
if __name__ == '__main__' :
    import sys
    import argparse
    
    argsp = argparse.ArgumentParser('Oxford ROS Player')
    argsp.add_argument('--dir', type=str, default=None, help='Directory of Oxford dataset')
    argsp.add_argument('--rate', type=float, default=1.0, help='Speed up/Slow down by rate factor')
    args = argsp.parse_args()
    
    rospy.init_node('oxford_player', anonymous=True)
    player = Player (args.dir, args.rate)
    poses = PosePlayer (player.dataset)
    images = ImagePlayer(player.dataset)
    player.add_data_player(poses)
    player.add_data_player(images)
    player.run()

