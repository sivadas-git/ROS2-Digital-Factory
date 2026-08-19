from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    # Declare launch arguments
    publisher_count_arg = DeclareLaunchArgument(
        'publisher_count',
        default_value='10',
        description='Number of publisher nodes to launch'
    )

    rate_arg = DeclareLaunchArgument(
        'rate',
        default_value='60.0',
        description='Publishing rate (Hz) per publisher'
    )

    publisher_count = LaunchConfiguration('publisher_count')
    rate = LaunchConfiguration('rate')

    # Use Python loop inside opaque function
    from launch.actions import OpaqueFunction

    def launch_nodes(context):
        count = int(context.launch_configurations['publisher_count'])
        pub_rate = float(context.launch_configurations['rate'])
        return [
            Node(
                package='my_tcp_listener',
                executable='ros2_scalability',
                name=f'scalability_publisher_{i}',
                output='screen',
                parameters=[
                    {'topic': f'rtt_test_topic_{i}'},
                    {'rate': pub_rate}
                ]
            ) for i in range(count)
        ]

    return LaunchDescription([
        publisher_count_arg,
        rate_arg,
        OpaqueFunction(function=launch_nodes)
    ])
