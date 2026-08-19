from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def launch_setup(context, *args, **kwargs):
    topic_count = int(LaunchConfiguration('topic_count').perform(context))

    return [
        Node(
            package='mqtt_bridge',
            executable='multi_topic_echo_responder',
            name=f'echo_responder_{i}',
            output='screen',
            parameters=[{'topic_index': i}]
        ) for i in range(topic_count)
    ]

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'topic_count',
            default_value='10',
            description='Number of MQTT echo responder nodes to launch'
        ),
        OpaqueFunction(function=launch_setup)
    ])
