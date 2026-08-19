from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    num_ports_arg = DeclareLaunchArgument(
        'num_ports',
        default_value='10',
        description='Number of TCP RTT publisher nodes to launch (starting from port 32101)'
    )

    def create_nodes(context):
        count = int(LaunchConfiguration('num_ports').perform(context))
        base_port = 32101
        rate = 10.0
        host = '192.168.1.4'

        nodes = []
        for i in range(count):
            port = base_port + i
            nodes.append(
                Node(
                    package='sensor_package',
                    executable='tcp_rtt_pub',
                    name=f'tcp_rtt_pub_{port}',
                    parameters=[
                        {'port': port},
                        {'rate': rate},
                        {'host': host},
                    ],
                    output='screen'
                )
            )
        return nodes

    return LaunchDescription([
        num_ports_arg,
        OpaqueFunction(function=create_nodes)
    ])
