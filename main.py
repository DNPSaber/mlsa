import os
import threading
import time
import socket
import struct
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from classification_detection import run
from SQL_auto import monitor_database
import xj
import schedule


def hourly_task():
    """每小时调用一次 xj 模块的主表获取和导航"""
    coordinates = xj.get_coordinates()
    if coordinates:
        xj.send_coordinates_via_ssh(coordinates)
    else:
        print("未获取到任何坐标数据")


# 检查文件是否已完全写入磁盘
def is_file_fully_written(file_path, check_interval=0.5, timeout=10):
    """
    检查文件是否已完全写入磁盘。
    :param file_path: 文件路径
    :param check_interval: 检查间隔（秒）
    :param timeout: 超时时间（秒）
    :return: 如果文件已完全写入返回 True，否则返回 False
    """
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        current_size = os.path.getsize(file_path)  # 获取文件大小
        if current_size == last_size:  # 如果文件大小在连续两次检查中未变化，认为写入完成
            return True
        last_size = current_size
        time.sleep(check_interval)  # 等待一段时间后再次检查

    return False  # 超时后仍未完成写入


# 处理图片文件
def process_image(file_path):
    """
    处理图片文件，调用分类检测函数并删除图片。
    :param file_path: 图片文件路径
    """
    if is_file_fully_written(file_path):  # 确保文件已完全写入
        try:
            run(file_path)  # 调用分类检测函数
            os.remove(file_path)  # 删除已处理的图片文件
            print(f"处理完成并删除图片: {file_path}")
        except Exception as e:
            print(f"处理图片时出错: {e}")
    else:
        print(f"文件未能完全写入: {file_path}")


# 自定义文件系统事件处理器
class ImageHandler(FileSystemEventHandler):
    """
    自定义文件系统事件处理器，用于检测新图片文件。
    """

    def __init__(self, queue):
        """
        初始化事件处理器。
        :param queue: 用于存储文件路径的队列
        """
        self.queue = queue

    def on_created(self, event):
        """
        当检测到新文件创建时触发。
        :param event: 文件系统事件
        """
        if not event.is_directory and event.src_path.endswith(('.jpg', '.png', '.jpeg')):  # 检测图片文件
            print(f"检测到新图片: {event.src_path}")
            self.queue.put(event.src_path)  # 将文件路径加入队列


# 启动图片接收服务器
def start_server(save_dir, port=12345):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # 如果目录不存在，则创建
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print('等待图片...')
    while True:
        conn, addr = s.accept()
        print('连接自:', addr)
        # 先接收文件名长度和文件名
        name_len = int.from_bytes(conn.recv(2), 'big')
        filename = conn.recv(name_len).decode()
        # 再接收文件大小和内容
        size = int.from_bytes(conn.recv(8), 'big')
        img_data = b''
        while len(img_data) < size:
            packet = conn.recv(4096)
            if not packet:
                break
            img_data += packet
        img_path = os.path.join(save_dir, filename)
        with open(img_path, 'wb') as f:
            f.write(img_data)
        print('图片已保存:', img_path)
        conn.close()


def worker():
    while True:
        file_path = file_queue.get()  # 从队列中获取文件路径
        if file_path is None:  # 如果收到 None，退出线程
            break
        process_image(file_path)  # 处理图片文件
        file_queue.task_done()  # 标记任务完成


schedule.every(1).hours.do(hourly_task)

if __name__ == "__main__":
    folder_to_watch = r'./old_tmp'  # 要监控的文件夹路径
    file_queue = Queue()  # 创建队列用于存储文件路径

    worker_thread = threading.Thread(target=worker)  # 创建工作线程
    worker_thread.daemon = True  # 设置为守护线程
    worker_thread.start()

    event_handler = ImageHandler(file_queue)  # 创建文件系统事件处理器
    observer = Observer()  # 创建文件系统观察者
    observer.schedule(event_handler, folder_to_watch, recursive=False)  # 监控指定文件夹

    database_thread = threading.Thread(target=monitor_database)  # 创建数据库监控线程
    database_thread.daemon = True  # 设置为守护线程
    database_thread.start()

    server_thread = threading.Thread(target=start_server, args=(folder_to_watch,))  # 创建图片接收服务器线程
    server_thread.daemon = True  # 设置为守护线程
    server_thread.start()

    print(f"开始监控文件夹: {folder_to_watch}")
    observer.start()  # 启动文件夹监控
    
    # while True:
    #     try:
    #         time.sleep(1)  # 主线程保持运行
    #     except KeyboardInterrupt:
    #         print("停止监控...")
    #         observer.stop()

    coordinates = xj.get_coordinates()
    if coordinates:
        xj.send_coordinates_via_ssh(coordinates)
    print("开始每小时调用 xj 模块...")
    while True:
        schedule.run_pending()
        time.sleep(1)
