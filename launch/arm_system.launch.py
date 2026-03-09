from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package="arm_controller", executable="arm_joint_publisher", name="arm_joint_publisher", output="screen"),
        Node(package="arm_controller", executable="force_sensor_node", name="force_sensor_node", output="screen"),
        Node(package="arm_controller", executable="safety_controller", name="safety_controller", output="screen"),
    ])
