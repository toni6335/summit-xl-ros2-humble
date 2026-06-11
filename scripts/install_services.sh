#!/bin/bash
set -e

# Instala los servicios systemd del proyecto Summit XL.
# Ejecutar desde la raíz del repositorio:
#   sudo bash scripts/install_services.sh

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Copiando script de arranque Pixhawk..."
cp "$REPO_DIR/scripts/arranqueauto_pixhawk.sh" /home/ros2/arranqueauto_pixhawk.sh
chmod +x /home/ros2/arranqueauto_pixhawk.sh
chown ros2:ros2 /home/ros2/arranqueauto_pixhawk.sh

echo "Copiando servicios systemd..."
cp "$REPO_DIR/services/"*.service /etc/systemd/system/

echo "Recargando systemd..."
systemctl daemon-reload

echo "Habilitando servicios..."
systemctl enable can0.service
systemctl enable pixhawk.service
systemctl enable summit_teleop.service
systemctl enable summit_nav2.service

echo "Instalación completada."
echo "Para arrancarlos ahora:"
echo "  sudo systemctl start can0.service"
echo "  sudo systemctl start pixhawk.service"
echo "  sudo systemctl start summit_teleop.service"
echo "  sudo systemctl start summit_nav2.service"
