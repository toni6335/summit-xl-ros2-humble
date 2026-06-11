#!/bin/bash

sleep 10

/home/ros2/.local/bin/mavproxy.py \
  --master=/dev/serial/by-id/usb-FTDI_TTL232R-3V3_FTAOXEYO-if00-port0 \
  --baudrate=1500000 \
  --out udp:127.0.0.1:14550 \
  --out udp:192.168.1.8:14550 \
  --daemon &

sleep 3

source /opt/ros/humble/setup.bash
source /home/ros2/ros2_ws/install/setup.bash

ros2 run mavros mavros_node --ros-args -p fcu_url:=udp://:14550@
