import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float64MultiArray

class SafetyController(Node):
    """
    The brain of the safety system.
    
    Subscribes to /arm/safety_status and makes decisions:
    - SAFE: allow arm to move normally
    - WARNING: slow down arm movement  
    - DANGER: send emergency stop command
    
    This is the node that would command the actual motors to stop
    in a real robot system.
    """

    def __init__(self):
        super().__init__('safety_controller')

        # Subscribe to safety status from force sensor node
        self.safety_subscription = self.create_subscription(
            String,
            '/arm/safety_status',
            self.safety_callback,
            10
        )

        # Publish arm commands (STOP, SLOW, NORMAL)
        self.command_publisher = self.create_publisher(
            String,
            '/arm/command',
            10
        )

        # Publish emergency stop signal
        self.estop_publisher = self.create_publisher(
            String,
            '/arm/estop',
            10
        )

        # Track system state
        self.current_state = 'NORMAL'
        self.estop_active = False
        self.danger_count = 0
        self.total_messages = 0

        # Statistics
        self.safe_count = 0
        self.warning_count = 0
        self.danger_count_total = 0

        self.get_logger().info('✅ Safety Controller started!')
        self.get_logger().info('Monitoring /arm/safety_status...')
        self.get_logger().info('=' * 50)

    def safety_callback(self, msg):
        """Process safety status and issue appropriate commands"""
        self.total_messages += 1
        parts = msg.data.split('|')
        status = parts[0]
        joint = parts[1] if len(parts) > 1 else 'unknown'
        force = parts[2] if len(parts) > 2 else '0Nm'

        if status == 'SAFE':
            self.safe_count += 1
            if self.current_state != 'NORMAL':
                # Recovering from warning/danger
                self.current_state = 'NORMAL'
                self.estop_active = False
                self.get_logger().info('✅ System SAFE — resuming normal operation')
            self.publish_command('NORMAL')

        elif status == 'WARNING':
            self.warning_count += 1
            self.current_state = 'SLOW'
            self.get_logger().warn(
                f'⚠️  WARNING detected on {joint} ({force}) — slowing arm'
            )
            self.publish_command('SLOW')

        elif status == 'DANGER':
            self.danger_count_total += 1
            self.current_state = 'STOPPED'

            if not self.estop_active:
                self.estop_active = True
                self.get_logger().error('=' * 50)
                self.get_logger().error(
                    f'🚨 EMERGENCY STOP TRIGGERED!'
                )
                self.get_logger().error(
                    f'   Cause: {joint} exceeded safe force limit ({force})'
                )
                self.get_logger().error(
                    f'   All joint movements HALTED'
                )
                self.get_logger().error('=' * 50)

            self.publish_command('STOP')
            self.publish_estop(joint, force)

        # Print statistics every 20 messages
        if self.total_messages % 20 == 0:
            self.get_logger().info(
                f'📊 Stats — Safe: {self.safe_count} | '
                f'Warning: {self.warning_count} | '
                f'Danger: {self.danger_count_total} | '
                f'Total: {self.total_messages}'
            )

    def publish_command(self, command):
        msg = String()
        msg.data = command
        self.command_publisher.publish(msg)

    def publish_estop(self, joint, force):
        msg = String()
        msg.data = f'ESTOP|{joint}|{force}'
        self.estop_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SafetyController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()