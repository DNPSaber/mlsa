import cv2
from ultralytics import YOLO
from paddleocr import PaddleOCR
import math
import numpy as np
import random
from save_sql import saves


# 使用 YOLO 模型检测指针
def zhizhen(image, model_path=r'./model/zhizhen.pt'):
    # 加载指针检测模型
    model = YOLO(model_path)
    # 对输入图像进行检测
    results = model(image)
    return results


# 使用 YOLO 模型检测数字
def shuzhi(image, model_path=r'./model/shuzhi.pt'):
    # 加载数字检测模型
    model = YOLO(model_path)
    # 对输入图像进行检测
    results = model(image)
    return results


# 使用 PaddleOCR 识别数字
def ocrshuzhi(image):
    # 初始化 OCR 模型
    ocr = PaddleOCR(use_angle_cls=True, lang='en', ocr_version='PP-OCRv4')
    # 对图像进行 OCR 识别
    result = ocr.ocr(image, cls=True)
    if result[0] is None:
        return None, None
    # 获取置信度最高的 OCR 结果
    max_ = max(result, key=lambda x: x[0][0][1][0])
    return max_[0][1][0], max_[0][1][1]


# 删除重复的 OCR 结果，保留置信度最高的
def delete_repeat_ocr_txt(num_dict):
    tmp_dict = {
        item['ocr_txt']: item
        for item in num_dict.values()
        if item['ocr_txt'] not in num_dict or item['ocr_score'] >= max(
            v['ocr_score'] for v in num_dict.values()
        )
    }
    return tmp_dict


# 对 OCR 结果按数字大小排序
def sort_num_dict(num_dict):
    # 按 OCR 识别的数字从大到小排序
    sorted_results = sorted(num_dict.values(), key=lambda x: float(x['ocr_txt']), reverse=True)
    ocr_txt_list = []
    for i, result in enumerate(sorted_results, start=0):
        result['index'] = i
        ocr_txt_list.append(result['ocr_txt'])
    # 返回排序后的字典和数字列表
    new_num_dict = {i: result for i, result in enumerate(sorted_results, start=0)}
    return new_num_dict, ocr_txt_list


# 筛选置信度最高的检测结果
def filter_highest_confidence_combined(results):
    highest_confidence = -1
    best_result = None

    for result in results:
        boxes = result.boxes
        keypoints = result.keypoints if hasattr(result, 'keypoints') else None

        for index, box in enumerate(boxes.data):
            confidence = box[4]
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_result = {
                    "bbox": box[:4],  # 边界框坐标
                    "keypoints": None
                }
                if keypoints is not None:
                    best_result["keypoints"] = keypoints.data[index]

    return best_result


# 检测仪表盘的读数
def detect_gauge_value(image_path, names, id_value, tran=True):
    # 读取输入图像
    image = cv2.imread(image_path)
    # 检测指针和数字
    zhizhen_results = zhizhen(image)
    shuzhi_results = shuzhi(image)
    image_trans = image
    zhizhen_results = filter_highest_confidence_combined(zhizhen_results)

    for i in shuzhi_results:
        delete_list = []
        num_dict = {}
        boxes = i.boxes
        for index, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            images = image[y1:y2, x1:x2]
            ocr_txt, ocr_score = ocrshuzhi(images)
            if ocr_txt is None:
                delete_list.append(index)
                continue
            rc_dict = {
                "index": index,
                "ocr_txt": ocr_txt,
                "ocr_score": ocr_score,
                "xy": (int(x1), int(y1), int(x2), int(y2))
            }
            num_dict[index] = rc_dict

        keypoints = i.keypoints
        for index, keypoint in enumerate(keypoints.data):
            if index in delete_list:
                continue

            for j in range(len(keypoint)):
                x, y = keypoint[j]
                x, y = int(x), int(y)
                num_dict[index]['keypoint'] = (x, y)

    pointer_result = {}

    keypoints = zhizhen_results['keypoints'][:, :2]
    keypoint_list = keypoints

    if len(keypoint_list) < 2:
        return None

    cent_x, cent_y = keypoint_list[1]
    head_x, head_y = keypoint_list[0]
    cent_x, cent_y = int(cent_x), int(cent_y)
    head_x, head_y = int(head_x), int(head_y)
    pointer_result['cent'] = (cent_x, cent_y)
    pointer_result['head'] = (head_x, head_y)

    if len(keypoint_list) >= 2:
        x0, y0 = keypoint_list[0]
        x1, y1 = keypoint_list[1]
        cv2.line(image_trans, (int(x0), int(y0)), (int(x1), int(y1)), (255, 0, 255), 4)

    num_dict = delete_repeat_ocr_txt(num_dict)
    common_ocr_degrees = [
        {"1.6": 45, "1.2": -22.5, "0.8": -90, "0.4": -157.5, "0": -225},
        {"10": 45, "8": -9, "6": -63, "4": -117, "2": -171, "0": -225},
        {"0.6": 45, "0.5": 0, "0.4": -45, "0.3": -90, "0.2": -135, "0.1": -180, "0": -225},
        {"25": 45, "20": -9, "15": -63, "10": -117, "5": -171, "0": -225}
    ]
    common_ocr_degree_first_end = [("1.6", "0"), ("10", "0"), ("0.6", "0"), ("25", "0")]
    final_right_index = None
    ocr_txt_list_list = []
    max_nums = 0
    for index, common_ocr_degree in enumerate(common_ocr_degrees):
        nums = 0
        ocr_txt_list = []
        for key, value in num_dict.items():
            try:
                float_ocr_txt = float(value['ocr_txt'])  # 转换为浮点数
            except Exception as e:
                continue
            for common_ocr in common_ocr_degree.keys():
                if float_ocr_txt == float(common_ocr):  # 匹配刻度
                    nums += 1
                    ocr_txt_list.append(common_ocr)
                    value["ocr_txt"] = common_ocr
        ocr_txt_list_list.append(ocr_txt_list)
        if nums >= 4:  # 如果匹配的刻度数大于等于 4，选择该映射关系
            final_right_index = index
            break
        if nums > max_nums:  # 更新最大匹配数
            max_nums = nums
            final_right_index = index

    # 如果未找到匹配的刻度映射关系，抛出错误
    try:
        if final_right_index is None:
            error_info = "没有找到匹配的标准列表"
            return ValueError(error_info)

        ocr_txt_list = ocr_txt_list_list[final_right_index]

        if len(ocr_txt_list) < 0:
            error_info = "任务检测出的刻度数小于2，直接判定为不清晰，无法读数"
            raise ValueError(error_info)
    except ValueError as e:
        print(e)
        return None, None

    # 删除不在匹配列表中的刻度
    delete_keys = []
    for key, value in num_dict.items():
        if value["ocr_txt"] not in ocr_txt_list:
            delete_keys.append(key)
    for key in delete_keys:
        num_dict.pop(key)

    # 计算指针与刻度的关系
    long_list, r = [], 300
    for index, value in enumerate(num_dict.values()):
        x, y = value['keypoint']
        long_list.append(math.sqrt((x - cent_x) ** 2 + (y - cent_y) ** 2))
        a, b = value['keypoint']
        r = np.mean(np.array(long_list))

    # 添加缺失的刻度
    end_txt, first_txt = common_ocr_degree_first_end[final_right_index]
    if end_txt not in ocr_txt_list:
        x = int(cent_x + r * math.cos(math.radians(45)))
        y = int(cent_y + r * math.sin(math.radians(45)))
        add_dict = {"index": 99, "ocr_txt": end_txt, "keypoint": (x, y)}
        num_dict[99] = add_dict

    if first_txt not in ocr_txt_list:
        x = int(cent_x + r * math.cos(math.radians(-225)))
        y = int(cent_y + r * math.sin(math.radians(-225)))
        add_dict = {"index": 100, "ocr_txt": first_txt, "keypoint": (x, y)}
        num_dict[100] = add_dict

    # 对刻度进行排序
    num_dict, ocr_txt_list = sort_num_dict(num_dict)
    degree_list = []
    degree_360_list = []

    # 如果刻度数小于 4，不进行透视变换
    if len(ocr_txt_list) < 4:
        tran = False

    # 透视变换处理
    if tran:
        new_point = {}
        old_point = {}
        right_change_dict = common_ocr_degrees[final_right_index]
        for index, (key, value) in enumerate(num_dict.items()):
            degree = right_change_dict[value['ocr_txt']]
            new_x = int(cent_x + r * math.cos(math.radians(degree)))
            new_y = int(cent_y + r * math.sin(math.radians(degree)))
            num_dict[key]['new_keypoint'] = (new_x, new_y)
            a, b = value['keypoint']
            old_point[value['ocr_txt']] = [a, b]
            new_point[value['ocr_txt']] = [new_x, new_y]

        choose_list = random.sample(ocr_txt_list, 4)
        choose_list = sorted(choose_list)
        src_points = np.array([old_point[choose_list[0]], old_point[choose_list[1]],
                               old_point[choose_list[2]], old_point[choose_list[3]]], dtype=np.float32)
        dst_points = np.array([new_point[choose_list[0]], new_point[choose_list[1]],
                               new_point[choose_list[2]], new_point[choose_list[3]]], dtype=np.float32)

        M = cv2.getPerspectiveTransform(src_points, dst_points)
        image_trans = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))

        def cvt_pos(pos, cvt_mat_t):
            u = pos[0]
            v = pos[1]
            x_ = (cvt_mat_t[0][0] * u + cvt_mat_t[0][1] * v + cvt_mat_t[0][2]) / (
                    cvt_mat_t[2][0] * u + cvt_mat_t[2][1] * v + cvt_mat_t[2][2])
            y_ = (cvt_mat_t[1][0] * u + cvt_mat_t[1][1] * v + cvt_mat_t[1][2]) / (
                    cvt_mat_t[2][0] * u + cvt_mat_t[2][1] * v + cvt_mat_t[2][2])
            return int(x_), int(y_)

        new_center_x, new_center_y = cvt_pos(pointer_result['cent'], M)
        new_head_x, new_head_y = cvt_pos(pointer_result['head'], M)
        r = math.atan2(new_head_y - new_center_y, new_head_x - new_center_x)
        d = math.degrees(r)
        d_360 = ((d + 360) % 360)

        for index, (key, value) in enumerate(num_dict.items()):
            trans_x, trans_y = cvt_pos(value['keypoint'], M)
            r1 = math.atan2(trans_y - new_center_y, trans_x - new_center_x)
            d1 = math.degrees(r1)
            d1_360 = ((d1 + 360) % 360)
            value['trans_keypoint'] = (trans_x, trans_y)
            value['degree'] = d1
            degree_list.append(d1)
            degree_360_list.append(d1_360)

    else:
        new_center_x, new_center_y = pointer_result['cent']
        new_head_x, new_head_y = pointer_result['head']
        r = math.atan2(new_head_y - new_center_y, new_head_x - new_center_x)
        d = math.degrees(r)
        d_360 = ((d + 360) % 360)
        for index, (key, value) in enumerate(num_dict.items()):
            trans_x, trans_y = value['keypoint']
            r1 = math.atan2(trans_y - new_center_y, trans_x - new_center_x)
            d1 = math.degrees(r1)
            d1_360 = ((d1 + 360) % 360)
            value['trans_keypoint'] = (trans_x, trans_y)
            value['degree'] = d1
            degree_list.append(d1)
            degree_360_list.append(d1_360)

    choose_index, bet_degree_n, bet_degree_p = None, None, None
    for index, value in enumerate(degree_360_list):
        if index + 1 == len(degree_360_list):
            break
        if degree_360_list[index] < degree_360_list[index + 1]:
            if 0 <= d_360 <= degree_360_list[index] or degree_360_list[index + 1] <= d_360 <= 360:
                bet_degree_n = 360 - degree_360_list[index + 1] + degree_360_list[index]
                if d_360 <= degree_360_list[index]:
                    bet_degree_p = 360 - degree_360_list[index + 1] + d_360
                else:
                    bet_degree_p = d_360 - degree_360_list[index + 1]
                choose_index = index
                break
        if degree_360_list[index + 1] <= d_360 <= degree_360_list[index]:
            bet_degree_n = degree_360_list[index] - degree_360_list[index + 1]
            bet_degree_p = d_360 - degree_360_list[index + 1]
            choose_index = index
            break

    a1, b1 = num_dict[choose_index]["trans_keypoint"]
    a2, b2 = num_dict[choose_index + 1]["trans_keypoint"]
    cv2.line(image_trans, (int(new_center_x), int(new_center_y)), (int(a1), int(b1)), (255, 0, 255), 5)
    cv2.line(image_trans, (int(new_center_x), int(new_center_y)), (int(a2), int(b2)), (255, 0, 255), 5)

    end_ocr_txt = float(num_dict[choose_index]["ocr_txt"])
    start_ocr_txt = float(num_dict[choose_index + 1]["ocr_txt"])

    final_result = start_ocr_txt + ((end_ocr_txt - start_ocr_txt) * (bet_degree_p / bet_degree_n))
    print("最终读数", final_result)
    cv2.imwrite(f'./jieguo/{names}.jpg', image_trans)
    saves(id_value, final_result, f'./jieguo/{names}.jpg', names)

    return final_result, image_trans


# 机械表检测主函数
def jixie(image_path, names, id_value):
    """
    检测机械表的读数。
    :param image_path: 输入图像路径
    :param names: 保存结果的文件名
    :param id_value: 数据库中主表的 ID 值
    :return: 最终读数和处理后的图像
    """
    try:
        final_result, image_trans = detect_gauge_value(image_path, names, id_value)
        if final_result is None:
            print("无法获取最终读数")
        return final_result, image_trans
    except Exception as e:
        print(f"检测过程中发生错误: {e}")
        return None, None


