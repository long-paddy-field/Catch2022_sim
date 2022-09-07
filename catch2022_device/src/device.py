#!/usr/bin/env python3
from cmath import pi
from email.header import Header
from shutil import move
from time import struct_time
import rospy
from typing import List
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import Float32
from std_msgs.msg import Int8MultiArray
from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import JointState
from std_msgs.msg import Int8
from std_msgs.msg import Bool
from std_msgs.msg import Empty
from std_msgs.msg import Header
# from cobs import cobs
import serial
import struct
import math
import serial.tools.list_ports

port = serial.tools.list_ports.comports()[0].device
# port="/dev/pts/4"
mode = "real"


class device():

    def __init__(self):
        self.setup()
        self.loop()

    def move_rad_callback(self, msg):
        self.move_deg[0] = msg.data[0]*180/math.pi
        self.move_deg[1] = msg.data[1]*180/math.pi
        # rospy.loginfo(uart_msg)
        # motor=struct.pack('<ff',*move_cmd)
        # self.uart.write(motor)
        # rospy.loginfo(motor)

    def servo_angle_callback(self, msg):
        self.servo_angle = msg.data*180/math.pi
        

    def stepper_state_callback(self, msg):
        self.stepper_state = msg.data.to_bytes(1, 'little')

    def pmp_state_callback(self, msg):
        self.pmp_state = msg.data

    def emergency_callback(self, msg):
        self.emergency = msg.data

    def is_blue_callback(self, msg):
        if msg.data == True:
            self.sign = 1
        else:
            self.sign = -1

    def setup(self):
        global port
        global mode
        self.uart = serial.Serial(port, 115200)

        self.pub_current_angle = rospy.Publisher('current_angle', Float32MultiArray, queue_size=1)
        self.pub_is_grabbed = rospy.Publisher('is_grabbed', Int8, queue_size=1)
        self.pub2 = rospy.Publisher('current_position', Float32MultiArray, queue_size=1)
        self.rviz_pub = rospy.Publisher("joint_states", JointState, queue_size=100)

        self.rviz_msg = JointState()
        self.rviz_msg.header = Header()
        self.rviz_msg.name = ['stand_arm1', 'arm1_arm2', 'arm2_linear', 'linear_wrist']

        self.rate = rospy.Rate(100)
        self.l1 = 0.6
        self.l2 = 0.3
        self.sign = 1

        # subscriberの宣言
        self.sub_move_rad = rospy.Subscriber('move_rad', Float32MultiArray, self.move_rad_callback, queue_size=1)
        self.sub_servo_cmd = rospy.Subscriber('servo_cmd', Bool, self.servo_angle_callback, queue_size=1)
        self.sub_stepper_state = rospy.Subscriber('stepper_state', Int8, self.stepper_state_callback, queue_size=1)
        self.sub_pmp_state = rospy.Subscriber('pmp_state', Bool, self.pmp_state_callback, queue_size=1)
        self.sub_emergency = rospy.Subscriber('emergency', Int8, self.emergency_callback, queue_size=1)
        self.sub_color_field = rospy.Subscriber('is_blue', Bool, self.is_blue_callback, queue_size=100)
        self.msg = Float32MultiArray(data=[1, 2])

        # 変数の初期化
        self.move_deg = [125, 138]
        self.move_cmd_theta = [90, 78]
        self.servo_angle = 0x00
        self.stepper_state = b'\x00'
        self.pmp_state = b'\x00'
        self.emergency = b'\x00'
        self.current_position = Float32MultiArray()

    def loop(self):
        while not rospy.is_shutdown():
            self.sendSerial()
            self.receiveSerial()
            # # if mode == "sim":
            #     self.current_angle = self.move_cmd_theta
            #     rospy.loginfo(self.current_angle)
            # self.rviz_msg.header.stamp = rospy.Time.now()
            # self.rviz_simulator()
            self.rate.sleep()

    def sendSerial(self):
        uart_msg = struct.pack("<fffc??c", *self.move_cmd, self.servo_angle, self.stepper_state, self.pmp_state, self.emergency, b'\xFF')
        rospy.loginfo(uart_msg)
        self.uart.write(uart_msg)

    def receiveSerial(self):
        # 受信と整形
        receiveData = self.uart.read(11)
        msg = struct.unpack("<ffccc", receiveData)
        if (not (msg[3] == b'\x00' and msg[4] == b'\xff')):
            print(self.uart.readline())
            return
        # rospy.loginfo(msg)
        self.current_angle = Float32MultiArray(data=[msg[0], msg[1]])
        self.current_position.data = self.theta_to_cartesian(self.current_angle.data)
        self.theta_to_cartesian([0.5, 0.5])
        is_grabbed = Int8(data=msg[2])
        self.pub_current_angle.publish(self.current_angle)
        self.pub_is_grabbed.publish(is_grabbed)

        self.pub2.publish(self.current_position)


if __name__ == "__main__":

    # try:
    rospy.init_node('device')
    rospy.loginfo("device : node is activated")
    # mode = rospy.get_param("mode")
    device = device()
    # except:
    #     rospy.loginfo("device : something wrong")
    # finally:
    #     rospy.loginfo("device : process end")
