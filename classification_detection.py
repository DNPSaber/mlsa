from ultralytics import YOLO
import cv2
import jixiebiao
import shuzibiao
import time
from pyzbar.pyzbar import decode
import sz_jiance

# 加载仪表检测模型
gauge_model = YOLO(r"./model/yibiao.pt")


def decode_qrcode(image_path):
    """
    解码输入图像中的二维码，并根据解码结果处理图像。
    :param image_path: 输入图像的路径
    """
    # 读取图像
    image = cv2.imread(image_path)
    # 解码二维码
    decoded_objects = decode(image)

    if decoded_objects:
        # 如果检测到二维码，提取其中的 ID 值并处理图像
        for obj in decoded_objects:
            id_value = f"{obj.data.decode('utf-8')}"  # 解码二维码数据为字符串
            process_image(image_path, id_value)  # 调用图像处理函数
    else:
        # 如果未检测到二维码，调用渗漏检测模块
        sz_jiance.run(image_path)


def process_image(image_path, id_value):
    """
    处理输入图像，检测仪表并根据分类结果进行相应处理。
    :param image_path: 输入图像的路径
    :param id_value: 从二维码中解码得到的 ID 值
    """
    # 读取图像
    image = cv2.imread(image_path)
    # 使用仪表检测模型进行检测
    results = gauge_model(image)
    # 获取当前时间戳，用于生成文件名
    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())

    for result in results:
        # 遍历检测结果中的每个检测框
        boxes = result.boxes
        for box in boxes:
            # 获取检测框的类别索引
            cls = int(box.cls[0])
            # 根据类别索引获取类别名称
            label = gauge_model.names[cls]
            if label == 'jixiebiao':
                # 如果检测到机械表，裁剪检测框区域并调用机械表处理函数
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # 获取检测框坐标
                cropped_path = f'./tmp/{timestamp}.jpg'  # 生成裁剪图像的保存路径
                cv2.imwrite(cropped_path, image[y1:y2, x1:x2])  # 保存裁剪后的图像
                jixiebiao.jixie(cropped_path, timestamp, id_value)  # 调用机械表处理函数
            elif label == 'shuzi':
                # 如果检测到数字表，调用数字表处理函数
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # 获取检测框坐标
                shuzibiao.shuziorc(x1, y1, x2, y2, image)  # 调用数字表处理函数
            else:
                # 如果未检测到适配的仪表类型，打印提示信息
                print('未检测到适配的仪表类型')


def run(image_path):
    """
    主运行函数，解码二维码并处理图像。
    :param image_path: 输入图像的路径
    """
    decode_qrcode(image_path)


if __name__ == '__main__':
    # 主程序入口，留空以便后续扩展
    pass
