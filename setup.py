from setuptools import find_packages, setup
import os
from glob import glob

package_name = "arm_controller"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="root",
    maintainer_email="root@todo.todo",
    description="ROS2 Robot Arm Controller with Safety System",
    license="MIT",
    extras_require={"test": ["pytest"]},
    entry_points={
        "console_scripts": [
            "arm_joint_publisher = arm_controller.arm_joint_publisher:main",
            "force_sensor_node = arm_controller.force_sensor_node:main",
            "safety_controller = arm_controller.safety_controller:main",
        ],
    },
)
