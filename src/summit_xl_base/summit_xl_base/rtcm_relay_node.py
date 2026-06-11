#!/usr/bin/env python3

import socket

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import RTCM


class RtcmRelay(Node):

    def __init__(self):
        super().__init__('rtcm_relay_node')

        self.host = '127.0.0.1'
        self.port = 5000

        self.pub = self.create_publisher(
            RTCM,
            '/mavros/gps_rtk/send_rtcm',
            10
        )

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)

        self.get_logger().info(
            f'Connecting to RTCM TCP server {self.host}:{self.port}'
        )

        self.sock.connect((self.host, self.port))
        self.sock.settimeout(0.1)

        self.timer = self.create_timer(0.02, self.timer_callback)

        self.get_logger().info('RTCM relay started')

    def timer_callback(self):
        try:
            data = self.sock.recv(180)

            if not data:
                return

            msg = RTCM()
            msg.data = list(data)
            self.pub.publish(msg)

        except socket.timeout:
            return

        except Exception as e:
            self.get_logger().error(f'RTCM relay error: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = RtcmRelay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
