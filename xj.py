import time

import pymysql
import paramiko

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '8507181ZZZzzz',
    'database': 'jiance',
    'charset': 'utf8mb4'
}

# 远程服务器配置
ssh_config = {
    'hostname': '192.168.82.104',
    'username': 'handsfree',
    'password': 'handsfree',
    'port': 22
}


def get_coordinates():
    """从数据库中获取主表的 x, y, z 坐标"""
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT x, y, yaw FROM main_table")
            return cursor.fetchall()
    except Exception as e:
        print(f"获取坐标时出错: {e}")
        return []
    finally:
        if connection:
            connection.close()


def send_coordinates_via_ssh(coordinates):
    """通过 SSH 将坐标发送到远程机器"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**ssh_config)
        print(coordinates)

        for x, y, z in coordinates:
            command = ("source /opt/ros/melodic/setup.bash && "
                       "source /home/handsfree/handsfree/vins_mono_ws/devel/setup.bash && "
                       "source /home/handsfree/handsfree/darknet_ros_ws/devel/setup.bash && "
                       "source /home/handsfree/handsfree/handsfree_ros_ws/devel/setup.bash && "
                       f"rosrun handsfree_tutorials nvdi.py --x {str(int(x)/1000)} --y {str(int(y)/1000)} --yaw {str(int(z)/1000)}")
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.read().decode())
            print(stderr.read().decode())
        time.sleep(10)
        ssh.exec_command("source /opt/ros/melodic/setup.bash && "
                         "source /home/handsfree/handsfree/vins_mono_ws/devel/setup.bash && "
                         "source /home/handsfree/handsfree/darknet_ros_ws/devel/setup.bash && "
                         "source /home/handsfree/handsfree/handsfree_ros_ws/devel/setup.bash && "
                         "rosrun handsfree_tutorials nvdi.py --x 0 --y 0 --yaw 0")
        print("所有导航完成，已返回原点")
    except Exception as e:
        print(f"通过 SSH 发送坐标时出错: {e}")
    finally:
        ssh.close()


if __name__ == "__main__":
    coordinates = get_coordinates()
    if coordinates:
        send_coordinates_via_ssh(coordinates)
