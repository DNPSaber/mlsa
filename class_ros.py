import threading
import paramiko
import soc
import SQL_auto
import automaticEntry


if __name__ == "__main__":
    controller = threading.Event()

    # 启动图片接收线程
    image_thread = threading.Thread(target=soc.receive_image, args=('E:\\mlsa\\imageod', 5001))
    image_thread.start()

    # 启动数据库监控线程
    sql_thread = threading.Thread(target=SQL_auto.monitor_database)
    sql_thread.start()


    