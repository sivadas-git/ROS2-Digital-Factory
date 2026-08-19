from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Declare CLI arguments
    topic_count_arg = DeclareLaunchArgument(
        'topic_count',
        default_value='10',
        description='Number of topics to listen for RTT logging'
    )

    timeout_sec_arg = DeclareLaunchArgument(
        'timeout_sec',
        default_value='2.0',
        description='Timeout duration for detecting losses'
    )

    # Substitution variables
    topic_count = LaunchConfiguration('topic_count')
    timeout_sec = LaunchConfiguration('timeout_sec')

    def launch_nodes(context):
        count = int(context.launch_configurations['topic_count'])
        timeout = float(context.launch_configurations['timeout_sec'])
        return [
            Node(
                package='sensor_package',  # Replace with your actual package name
                executable='multi_topic_rtt_logger',
                name=f'rtt_logger_{i}',
                output='screen',
                parameters=[
                    {'topic_index': i},
                    {'timeout_sec': timeout}
                ]
            ) for i in range(count)
        ]

    return LaunchDescription([
        topic_count_arg,
        timeout_sec_arg,
        OpaqueFunction(function=launch_nodes)
    ])
