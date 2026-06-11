from launch import LaunchDescription
from launch_ros.actions import Node
from pathlib import Path


def generate_launch_description():

    config_file = str(
        Path.home() / 'ros2_ws/src/summit_xl_base/config/ps4.config.yaml'
    )

    return LaunchDescription([

        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen'
        ),

        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_twist_joy_node',
            parameters=[config_file],
            output='screen'
        ),

        Node(
            package='summit_xl_base',
            executable='base_node',
            name='summit_base',
            output='screen'
        ),
        
        Node(
    	    package='summit_xl_base',
            executable='pixhawk_nav_odom',
            name='pixhawk_nav_odom',
            output='screen'
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom_static',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
            output='screen'
        ),
        
        Node(
    	    package='summit_xl_base',
            executable='map_data_republisher',
            name='map_data_republisher',
            output='screen'
        ),
 	
 	
        
        
        
        
  
    ])
