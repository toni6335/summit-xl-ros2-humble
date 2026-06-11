#!/usr/bin/env python3

import math
import can

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster


class SummitBase(Node):

    def __init__(self):
        super().__init__('summit_base')

        self.bus = can.interface.Bus(
            channel='can0',
            interface='socketcan'
        )

        # Parámetros robot
        self.WHEEL_SEPARATION = 1
        self.METERS_PER_COUNT = 0.00001931

        # Odometría
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0

        self.last_left_pos = None
        self.last_right_pos = None
        self.last_odom_time = self.get_clock().now()

        self.last_cmd_time = self.get_clock().now()

        self.cmd_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_callback,
            10
        )

        self.odom_pub = self.create_publisher(
            Odometry,
            '/odom',
            10
        )

        #self.tf_broadcaster = TransformBroadcaster(self)

        self.watchdog_timer = self.create_timer(
            0.1,
            self.watchdog_callback
        )

        self.odom_timer = self.create_timer(
            0.05,
            self.odom_callback
        )

        self.get_logger().info("Summit XL Base Controller with Odometry Started")

    def cmd_callback(self, msg):
        self.last_cmd_time = self.get_clock().now()

        v = msg.linear.x
        w = msg.angular.z

        left_speed = v - (w * self.WHEEL_SEPARATION / 2.0)
        right_speed = v + (w * self.WHEEL_SEPARATION / 2.0)

        left_cmd = int(left_speed * 300000)
        right_cmd = int(right_speed * 300000)

        self.send_motor_command(1, left_cmd)
        self.send_motor_command(2, left_cmd)
        self.send_motor_command(3, right_cmd)
        self.send_motor_command(4, right_cmd)

    def send_motor_command(self, motor_id, speed):
        can_id = 0x600 + motor_id

        if motor_id in [3, 4]:
            speed = -speed

        speed_bytes = int(speed).to_bytes(
            4,
            byteorder='little',
            signed=True
        )

        data = bytearray([
            0x23,
            0xFF, 0x60,
            0x00
        ])

        data.extend(speed_bytes)

        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=False
        )

        try:
            self.bus.send(msg)
        except can.CanError:
            self.get_logger().error(f"CAN send failed motor {motor_id}")

    def read_position(self, motor_id):
        request_id = 0x600 + motor_id
        response_id = 0x580 + motor_id

        request = can.Message(
            arbitration_id=request_id,
            data=[0x40, 0x64, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00],
            is_extended_id=False
        )

        try:
            self.bus.send(request)
        except can.CanError:
            return None

        timeout_time = self.get_clock().now().nanoseconds + int(0.02 * 1e9)

        while self.get_clock().now().nanoseconds < timeout_time:
            msg = self.bus.recv(timeout=0.005)

            if msg is None:
                continue

            if msg.arbitration_id == response_id:
                data = bytes(msg.data)

                if len(data) == 8 and data[1] == 0x64 and data[2] == 0x60:
                    value = int.from_bytes(
                        data[4:8],
                        byteorder='little',
                        signed=True
                    )
                    return value

        return None

    def odom_callback(self):
        now = self.get_clock().now()

        p1 = self.read_position(1)
        p2 = self.read_position(2)
        p3 = self.read_position(3)
        p4 = self.read_position(4)

        if None in [p1, p2, p3, p4]:
            return

        # Invertir lado derecho para que avance positivo
        left_pos = (p1 + p2) / 2.0
        right_pos = (-(p3) + -(p4)) / 2.0

        if self.last_left_pos is None:
            self.last_left_pos = left_pos
            self.last_right_pos = right_pos
            self.last_odom_time = now
            return

        delta_left_counts = left_pos - self.last_left_pos
        delta_right_counts = right_pos - self.last_right_pos

        self.last_left_pos = left_pos
        self.last_right_pos = right_pos

        dt = (now - self.last_odom_time).nanoseconds / 1e9
        self.last_odom_time = now

        if dt <= 0.0:
            return

        dl = delta_left_counts * self.METERS_PER_COUNT
        dr = delta_right_counts * self.METERS_PER_COUNT

        dc = (dr + dl) / 2.0
        dth = (dr - dl) / self.WHEEL_SEPARATION

        self.x += dc * math.cos(self.th + dth / 2.0)
        self.y += dc * math.sin(self.th + dth / 2.0)
        self.th += dth

        vx = dc / dt
        vth = dth / dt

        qz = math.sin(self.th / 2.0)
        qw = math.cos(self.th / 2.0)

        odom_msg = Odometry()
        odom_msg.header.stamp = now.to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'

        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation.z = qz
        odom_msg.pose.pose.orientation.w = qw

        odom_msg.twist.twist.linear.x = vx
        odom_msg.twist.twist.angular.z = vth

        self.odom_pub.publish(odom_msg)

        tf_msg = TransformStamped()
        tf_msg.header.stamp = now.to_msg()
        tf_msg.header.frame_id = 'odom'
        tf_msg.child_frame_id = 'base_link'

        tf_msg.transform.translation.x = self.x
        tf_msg.transform.translation.y = self.y
        tf_msg.transform.translation.z = 0.0
        tf_msg.transform.rotation.z = qz
        tf_msg.transform.rotation.w = qw

        #self.tf_broadcaster.sendTransform(tf_msg)

    def watchdog_callback(self):
        now = self.get_clock().now()
        dt = (now - self.last_cmd_time).nanoseconds / 1e9

        if dt > 0.5:
            self.send_motor_command(1, 0)
            self.send_motor_command(2, 0)
            self.send_motor_command(3, 0)
            self.send_motor_command(4, 0)


def main(args=None):
    rclpy.init(args=args)
    node = SummitBase()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
