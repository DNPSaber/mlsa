import os
import pymysql
from pyzbar.pyzbar import decode
from PIL import Image

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '8507181ZZZzzz',
    'database': 'jiance',
    'charset': 'utf8mb4'
}


def execute_query(query, params=None):
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()
    except Exception as e:
        print(f"执行查询时出错: {e}")
    finally:
        if connection:
            connection.close()


def process_images(folder_path="E:\\mlsa\\imageod"):
    if not os.path.exists(folder_path):
        print(f"文件夹 {folder_path} 不存在")
        return

    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            try:
                # 去除文件名后缀
                file_name_no_ext = os.path.splitext(file_name)[0]
                # 提取文件名中的 x, y, yaw 值
                parts = file_name_no_ext.split('_')
                if len(parts) != 3 or not parts[0].startswith('x') or not parts[1].startswith('y') or not parts[
                    2].startswith('yaw'):
                    print(f"文件名格式不正确: {file_name}")
                    continue

                x = parts[0][1:]  # 去掉 'x'
                y = parts[1][1:]  # 去掉 'y'
                z = parts[2][3:]  # 去掉 'yaw'

                # 检测二维码
                file_path = os.path.join(folder_path, file_name)
                image = Image.open(file_path)
                qr_codes = decode(image)

                if qr_codes:
                    for qr in qr_codes:
                        name = qr.data.decode('utf-8')  # 获取二维码数据
                        # 插入数据到数据库
                        insert_query = """
                                       INSERT INTO main_table (name, x, y, yaw, max, min)
                                       VALUES (%s, %s, %s, %s, %s, %s) \
                                       """
                        execute_query(insert_query, (name, x, y, z, '1.4', '0.2'))
                        print(f"图片 {file_name} 的二维码数据 {name} 已插入数据库")
                else:
                    print(f"图片 {file_name} 中未检测到二维码")

            except Exception as e:
                print(f"处理图片 {file_name} 时出错: {e}")


if __name__ == '__main__':
    folder_path = "E:\\mlsa\\imageod"  # 图片存放目录
    process_images(folder_path)
