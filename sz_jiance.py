import cv2
from ultralytics import YOLO
import time


def detect_and_annotate(image_path):
    """
    检测图像中的标签，并在检测到的标签上绘制标注框，展示并保存结果。
    :param image_path: 输入图像路径
    """
    output_path = f"./tmp/annotated_{time.strftime('%Y%m%d%H%M%S')}.jpg"  # 输出图像路径
    # 加载模型
    model = YOLO(r"./model/sz.pt")
    # 读取图像
    image = cv2.imread(image_path)
    # 使用模型进行检测
    results = model(image)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            # 获取检测框的类别索引和名称
            cls = int(box.cls[0])
            label = model.names[cls]
            # 获取检测框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # 在图像上绘制矩形框和标签
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 展示标注后的图像
    cv2.imshow("Annotated Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 保存标注后的图像
    cv2.imwrite(output_path, image)
