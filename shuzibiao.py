import cv2
from paddleocr import PaddleOCR


# 定义一个函数，用于对图像中的指定区域进行 OCR 检测
def shuziorc(x1, y1, x2, y2, image):
    """
    对图像中的指定区域进行 OCR 检测，并显示检测结果。
    :param x1: 检测区域左上角的 x 坐标
    :param y1: 检测区域左上角的 y 坐标
    :param x2: 检测区域右下角的 x 坐标
    :param y2: 检测区域右下角的 y 坐标
    :param image: 输入的图像
    """
    lists = []  # 用于存储检测到的数字结果
    # 裁剪图像，获取指定区域
    cropped_image = image[y1:y2, x1:x2]

    # 显示裁剪后的图像，用于调试
    cv2.imshow('cropped_image', cropped_image)
    cv2.waitKey(0)  # 等待用户按键关闭窗口
    cv2.destroyAllWindows()  # 关闭所有窗口

    # 初始化 PaddleOCR 模型
    ocr = PaddleOCR(use_angle_cls=True, lang='en', ocr_version='PP-OCRv4')
    # 对裁剪后的图像进行 OCR 检测
    result = ocr.ocr(cropped_image, cls=True)

    try:
        # 遍历 OCR 检测结果
        for line in result[0]:
            # 打印检测到的数字
            print(f"检测到的数字: {line[1][0]}")
    except TypeError:
        # 如果未检测到任何结果，打印提示信息
        print('没有检测到数字')

    # 打印检测结果列表（目前未使用）
    print(lists)

    # 在原始图像上绘制检测区域的矩形框
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # 显示绘制了矩形框的图像
    cv2.imshow("Detected Image", image)
    cv2.waitKey(0)  # 等待用户按键关闭窗口
    cv2.destroyAllWindows()  # 关闭所有窗口
