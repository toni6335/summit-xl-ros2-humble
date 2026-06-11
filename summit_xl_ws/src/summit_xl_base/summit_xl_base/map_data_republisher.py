#!/usr/bin/env python3

import copy
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException


def q_mult(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2

    return [
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    ]


def q_conj(q):
    return [-q[0], -q[1], -q[2], q[3]]


def rotate_vector(v, q):
    qv = [v.x, v.y, v.z, 0.0]
    qr = q_mult(q_mult(q, qv), q_conj(q))

    out = Vector3()
    out.x = qr[0]
    out.y = qr[1]
    out.z = qr[2]
    return out


def quat_from_msg(q):
    return [q.x, q.y, q.z, q.w]


def quat_to_msg(q_list, q_msg):
    q_msg.x = q_list[0]
    q_msg.y = q_list[1]
    q_msg.z = q_list[2]
    q_msg.w = q_list[3]


class MapDataRepublisher(Node):

    def __init__(self):
        super().__init__('map_data_republisher')

        qos_in = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        qos_out = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.odom_pub = self.create_publisher(
            Odometry,
            '/odom_in_map',
            qos_out
        )

        self.imu_pub = self.create_publisher(
            Imu,
            '/imu_in_map',
            qos_out
        )

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            qos_in
        )

        self.create_subscription(
            Imu,
            '/mavros/imu/data',
            self.imu_callback,
            qos_in
        )

        self.get_logger().info(
            'Publishing /odom_in_map and /imu_in_map'
        )

    def clean_frame(self, frame):
        if frame.startswith('/'):
            return frame[1:]
        return frame

    def lookup_tf(self, target_frame, source_frame):
        return self.tf_buffer.lookup_transform(
            target_frame,
            source_frame,
            rclpy.time.Time()
        )

    def odom_callback(self, msg):
        try:
            out = copy.deepcopy(msg)

            source_frame = self.clean_frame(msg.header.frame_id)

            tf_map_source = self.lookup_tf('map', source_frame)

            q_tf = quat_from_msg(tf_map_source.transform.rotation)
            q_odom = quat_from_msg(msg.pose.pose.orientation)

            p = msg.pose.pose.position

            v = Vector3()
            v.x = p.x
            v.y = p.y
            v.z = p.z

            p_rot = rotate_vector(v, q_tf)

            out.header.frame_id = 'map'
            out.child_frame_id = self.clean_frame(msg.child_frame_id)

            out.pose.pose.position.x = p_rot.x + tf_map_source.transform.translation.x
            out.pose.pose.position.y = p_rot.y + tf_map_source.transform.translation.y
            out.pose.pose.position.z = p_rot.z + tf_map_source.transform.translation.z

            q_out = q_mult(q_tf, q_odom)
            quat_to_msg(q_out, out.pose.pose.orientation)

            out.twist.twist.linear = rotate_vector(msg.twist.twist.linear, q_tf)
            out.twist.twist.angular = rotate_vector(msg.twist.twist.angular, q_tf)

            self.odom_pub.publish(out)

        except (LookupException, ConnectivityException, ExtrapolationException):
            return

    def imu_callback(self, msg):
        try:
            out = copy.deepcopy(msg)

            source_frame = self.clean_frame(msg.header.frame_id)

            tf_map_source = self.lookup_tf('map', source_frame)
            q_tf = quat_from_msg(tf_map_source.transform.rotation)

            q_imu = quat_from_msg(msg.orientation)
            q_out = q_mult(q_tf, q_imu)

            out.header.frame_id = 'map'
            quat_to_msg(q_out, out.orientation)

            out.angular_velocity = rotate_vector(msg.angular_velocity, q_tf)
            out.linear_acceleration = rotate_vector(msg.linear_acceleration, q_tf)

            self.imu_pub.publish(out)

        except (LookupException, ConnectivityException, ExtrapolationException):
            return


def main(args=None):
    rclpy.init(args=args)
    node = MapDataRepublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
