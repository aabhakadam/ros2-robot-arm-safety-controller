import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import math
import time

class ArmJointPublisher(Node):
    """
    Simulates a 6-DOF robot arm by publishing joint angles.
    Each joint angle changes over time to simulate arm movement.
    """

    def __init__(self):
        # Initialize the node with a name
        super().__init__('arm_joint_publisher')

        # Create a publisher on the topic '/arm/joint_states'
        # Float64MultiArray lets us send an array of 6 floats (one per joint)
        self.publisher = self.create_publisher(
            Float64MultiArray,
            '/arm/joint_states',
            10  # queue size
        )

        # Create a timer that calls self.publish_joints every 0.5 seconds
        self.timer = self.create_timer(0.5, self.publish_joints)

        # Track time to animate joint movement
        self.start_time = time.time()

        self.get_logger().info('✅ Arm Joint Publisher started!')
        self.get_logger().info('Publishing to /arm/joint_states every 0.5s')

    def publish_joints(self):
        """Calculate and publish current joint angles"""
        elapsed = time.time() - self.start_time

        # Simulate 6 joints moving in sine waves at different speeds
        # In a real arm these would come from encoder readings
        joint_angles = [
            math.sin(elapsed * 0.5) * 45,           # Joint 1 - base rotation
            math.sin(elapsed * 0.3 + 1.0) * 30,     # Joint 2 - shoulder
            math.sin(elapsed * 0.4 + 2.0) * 60,     # Joint 3 - elbow
            math.sin(elapsed * 0.6 + 0.5) * 45,     # Joint 4 - wrist rotation
            math.sin(elapsed * 0.7 + 1.5) * 30,     # Joint 5 - wrist bend
            math.sin(elapsed * 0.2 + 3.0) * 20,     # Joint 6 - gripper rotation
        ]

        # Build the message
        msg = Float64MultiArray()
        msg.data = joint_angles

        # Publish it
        self.publisher.publish(msg)

        # Log every 5 seconds so we don't spam the terminal
        if int(elapsed) % 5 == 0:
            self.get_logger().info(
                f'Joint angles (degrees): ' +
                ', '.join([f'J{i+1}:{a:.1f}°' for i, a in enumerate(joint_angles)])
            )


def main(args=None):
    rclpy.init(args=args)           # Initialize ROS2
    node = ArmJointPublisher()      # Create our node
    rclpy.spin(node)                # Keep it running
    node.destroy_node()             # Cleanup on exit
    rclpy.shutdown()


if __name__ == '__main__':
    main()