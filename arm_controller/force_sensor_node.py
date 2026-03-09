import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String
import random
import math

class ForceSensorNode(Node):
    """
    Simulates force/torque sensors on each joint of the robot arm.
    
    Subscribes to joint states, calculates simulated force based on
    joint velocity (change in angle), and publishes force readings.
    Detects dangerous force spikes and publishes safety warnings.
    """

    def __init__(self):
        super().__init__('force_sensor_node')

        # Subscribe to joint states from arm_joint_publisher
        self.joint_subscription = self.create_subscription(
            Float64MultiArray,
            '/arm/joint_states',
            self.joint_callback,
            10
        )

        # Publish force readings
        self.force_publisher = self.create_publisher(
            Float64MultiArray,
            '/arm/force_data',
            10
        )

        # Publish safety status as a string message
        self.safety_publisher = self.create_publisher(
            String,
            '/arm/safety_status',
            10
        )

        # Store previous joint angles to calculate velocity
        self.previous_angles = None
        self.message_count = 0

        # Force thresholds (Newton-meters, simulated)
        self.WARNING_THRESHOLD = 15.0
        self.DANGER_THRESHOLD = 25.0

        self.get_logger().info('✅ Force Sensor Node started!')
        self.get_logger().info('Subscribed to /arm/joint_states')
        self.get_logger().info('Publishing to /arm/force_data and /arm/safety_status')

    def joint_callback(self, msg):
        """Called every time a new joint state message arrives"""
        current_angles = list(msg.data)
        self.message_count += 1

        # Calculate joint velocities (how fast each joint is moving)
        if self.previous_angles is not None:
            velocities = [
                abs(current - prev)
                for current, prev in zip(current_angles, self.previous_angles)
            ]

            # Simulate force based on velocity + random sensor noise
            # In a real system this comes from actual force/torque sensors
            forces = [
                v * 2.5 + random.uniform(0, 3.0)
                for v in velocities
            ]

            # Inject a random force spike every ~30 messages to simulate
            # the arm hitting an unexpected obstacle
            if self.message_count % 30 == 0:
                spike_joint = random.randint(0, 5)
                forces[spike_joint] = random.uniform(28.0, 45.0)
                self.get_logger().warn(
                    f'⚠️  Simulated obstacle impact on Joint {spike_joint + 1}!'
                )

            # Publish force readings
            force_msg = Float64MultiArray()
            force_msg.data = forces
            self.force_publisher.publish(force_msg)

            # Check safety status
            max_force = max(forces)
            max_joint = forces.index(max_force) + 1

            safety_msg = String()

            if max_force >= self.DANGER_THRESHOLD:
                safety_msg.data = f'DANGER|Joint {max_joint}|{max_force:.1f}Nm'
                self.get_logger().error(
                    f'🚨 DANGER: Joint {max_joint} force = {max_force:.1f}Nm — STOP ARM!'
                )
            elif max_force >= self.WARNING_THRESHOLD:
                safety_msg.data = f'WARNING|Joint {max_joint}|{max_force:.1f}Nm'
                self.get_logger().warn(
                    f'⚠️  WARNING: Joint {max_joint} force = {max_force:.1f}Nm'
                )
            else:
                safety_msg.data = f'SAFE|all|{max_force:.1f}Nm'

            self.safety_publisher.publish(safety_msg)

        # Store current angles for next iteration
        self.previous_angles = current_angles


def main(args=None):
    rclpy.init(args=args)
    node = ForceSensorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()