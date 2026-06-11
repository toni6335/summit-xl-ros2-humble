from glob import glob
from setuptools import find_packages, setup
import os

package_name = 'summit_xl_base'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Antonio Fernandez',
    maintainer_email='antoniofernandezferia@gmail.com',
    description='ROS2 Humble package for controlling and testing autonomous navigation on a Robotnik Summit XL platform.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'base_node = summit_xl_base.base_node:main',
            'rtcm_relay_node = summit_xl_base.rtcm_relay_node:main',
            'pixhawk_nav_odom = summit_xl_base.pixhawk_nav_odom:main',
            'map_data_republisher = summit_xl_base.map_data_republisher:main',
        ],
    },
)
