# Summit XL TFG - ROS2 Humble

Repositorio del TFG para la puesta en marcha, teleoperación y navegación autónoma de una plataforma **Robotnik Summit XL** usando **ROS2 Humble**.

El proyecto contiene un paquete ROS2 propio (`summit_xl_base`) y varios servicios `systemd` para automatizar el arranque del robot.

## Contenido del repositorio

```text
.
├── src/
│   └── summit_xl_base/
│       ├── summit_xl_base/
│       │   ├── base_node.py
│       │   ├── pixhawk_nav_odom.py
│       │   ├── map_data_republisher.py
│       │   └── rtcm_relay_node.py
│       ├── config/
│       │   ├── nav2_no_obstacles.yaml
│       │   ├── ps4.config.yaml
│       │   └── summit.rviz
│       └── launch/
│           └── teleop_bringup.launch.py
├── services/
│   ├── can0.service
│   ├── pixhawk.service
│   ├── summit_teleop.service
│   └── summit_nav2.service
├── scripts/
│   ├── arranqueauto_pixhawk.sh
│   └── install_services.sh
└── README.md
```

## Descripción general

Este workspace permite:

- Controlar los motores del Summit XL mediante **SocketCAN/CANopen**.
- Publicar odometría del robot en `/odom`.
- Recibir comandos de velocidad desde `/cmd_vel`.
- Usar un mando PS4 mediante `joy` y `teleop_twist_joy`.
- Conectar la Pixhawk mediante MAVProxy y MAVROS.
- Republicar la odometría de MAVROS en `/odom_pixhawk`.
- Lanzar Nav2 con una configuración inicial sin obstáculos.
- Preparar el arranque automático mediante servicios `systemd`.

## Nodos principales

### `base_node.py`

Nodo principal de control de la base móvil.

- Suscribe: `/cmd_vel`
- Publica: `/odom`
- Usa interfaz CAN: `can0`
- Envía comandos a los motores mediante CANopen.
- Calcula odometría a partir de las posiciones de las ruedas.
- Incluye un watchdog para detener el robot si dejan de llegar comandos.

### `pixhawk_nav_odom.py`

Convierte la odometría local de MAVROS en una odometría útil para Nav2.

- Suscribe: `/mavros/local_position/odom`
- Publica: `/odom_pixhawk`
- Publica TF: `odom -> base_link`
- Elimina movimiento vertical y deja el movimiento en 2D.

### `map_data_republisher.py`

Republica datos de odometría e IMU transformados al frame `map`.

- Publica: `/odom_in_map`
- Publica: `/imu_in_map`

### `rtcm_relay_node.py`

Nodo auxiliar para reenviar correcciones RTCM hacia MAVROS.

- Publica: `/mavros/gps_rtk/send_rtcm`

## Requisitos

Sistema probado para:

- Ubuntu 22.04
- ROS2 Humble
- Python 3
- SocketCAN
- MAVROS
- MAVProxy
- Nav2
- `joy`
- `teleop_twist_joy`
- `python-can`

Instalación orientativa:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-mavros \
  ros-humble-mavros-extras \
  ros-humble-nav2-bringup \
  ros-humble-navigation2 \
  ros-humble-joy \
  ros-humble-teleop-twist-joy \
  python3-colcon-common-extensions \
  can-utils

pip install python-can MAVProxy
```

También puede ser necesario instalar los datasets de MAVROS:

```bash
sudo /opt/ros/humble/lib/mavros/install_geographiclib_datasets.sh
```

## Compilación del workspace

Desde la raíz del workspace:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Para dejarlo cargado automáticamente:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

## Uso manual

### 1. Activar CAN

```bash
sudo ip link set can0 up type can bitrate 1000000
```

Comprobación:

```bash
ip link show can0
```

### 2. Lanzar teleoperación y nodos base

```bash
ros2 launch summit_xl_base teleop_bringup.launch.py
```

Este launch inicia:

- `joy_node`
- `teleop_twist_joy_node`
- `base_node`
- `pixhawk_nav_odom`
- `map_data_republisher`
- Transformada estática `map -> odom`

### 3. Lanzar Nav2

```bash
ros2 launch nav2_bringup navigation_launch.py \
  use_sim_time:=false \
  params_file:=~/ros2_ws/src/summit_xl_base/config/nav2_no_obstacles.yaml
```

### 4. Abrir RViz2

```bash
rviz2 -d ~/ros2_ws/src/summit_xl_base/config/summit.rviz
```

## Servicios systemd

Los servicios incluidos permiten arrancar automáticamente las partes principales del sistema.

### Servicios incluidos

| Servicio | Función |
|---|---|
| `can0.service` | Activa la interfaz CAN `can0` a 1 Mbit/s |
| `pixhawk.service` | Ejecuta el script de arranque de MAVProxy y MAVROS |
| `summit_teleop.service` | Lanza teleoperación, control base y nodos auxiliares |
| `summit_nav2.service` | Lanza Nav2 con la configuración del proyecto |

### Instalación automática de servicios

Desde la raíz del repositorio:

```bash
sudo bash scripts/install_services.sh
```

### Arranque manual de servicios

```bash
sudo systemctl start can0.service
sudo systemctl start pixhawk.service
sudo systemctl start summit_teleop.service
sudo systemctl start summit_nav2.service
```

### Ver estado

```bash
systemctl status can0.service
systemctl status pixhawk.service
systemctl status summit_teleop.service
systemctl status summit_nav2.service
```

### Ver logs

```bash
journalctl -u pixhawk.service -f
journalctl -u summit_teleop.service -f
journalctl -u summit_nav2.service -f
```

### Reiniciar servicios

```bash
sudo systemctl restart pixhawk.service
sudo systemctl restart summit_teleop.service
sudo systemctl restart summit_nav2.service
```

## Configuración de red y ROS2

Los servicios usan:

```text
ROS_DOMAIN_ID=0
ROS_LOCALHOST_ONLY=0
RMW_IMPLEMENTATION=rmw_fastrtps_cpp
FASTDDS_BUILTIN_TRANSPORTS=UDPv4
```

Esto permite compartir información ROS2 por red usando Fast DDS.

## Subir el proyecto a GitHub

### 1. Crear repositorio en GitHub

En GitHub, crea un repositorio nuevo, por ejemplo:

```text
summit-xl-tfg-ros2
```

No hace falta marcar la opción de crear README, porque este repositorio ya lo incluye.

### 2. Inicializar Git en el workspace

```bash
cd ~/ros2_ws
git init
git add .
git commit -m "Initial commit: Summit XL ROS2 TFG workspace"
```

### 3. Conectar con GitHub

Sustituye `TU_USUARIO` y `NOMBRE_REPO`:

```bash
git branch -M main
git remote add origin https://github.com/TU_USUARIO/NOMBRE_REPO.git
git push -u origin main
```

Ejemplo:

```bash
git remote add origin https://github.com/TU_USUARIO/summit-xl-tfg-ros2.git
git push -u origin main
```

Si GitHub pide usuario y contraseña, usa un **Personal Access Token** en lugar de la contraseña.

## Comandos útiles

Ver nodos activos:

```bash
ros2 node list
```

Ver tópicos:

```bash
ros2 topic list
```

Ver comandos de velocidad:

```bash
ros2 topic echo /cmd_vel
```

Ver odometría:

```bash
ros2 topic echo /odom
ros2 topic echo /odom_pixhawk
```

Ver transformadas:

```bash
ros2 run tf2_tools view_frames
```

## Notas importantes

- La ruta del usuario usada en los servicios es `/home/ros2`.
- La Pixhawk se conecta mediante el puerto indicado en `arranqueauto_pixhawk.sh`.
- La IP `192.168.1.8` aparece como salida UDP para enviar datos MAVLink a otro equipo.
- Si se cambia el usuario, el puerto serie, la IP o la ruta del workspace, deben actualizarse los archivos de `services/` y `scripts/`.
- La configuración actual de Nav2 está pensada para navegación inicial sin mapa de obstáculos real.
- Para navegación autónoma completa con evitación de obstáculos se debe integrar correctamente el LiDAR en los costmaps.

## Autor

Antonio Fernández Feria  
Trabajo Fin de Grado - Ingeniería Electrónica Industrial
