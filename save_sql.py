import pymysql

# 数据库配置字典，包含连接数据库所需的参数
db_config = {
    'host': 'localhost',  # 数据库主机地址
    'user': 'root',  # 数据库用户名
    'password': '8507181ZZZzzz',  # 数据库密码
    'database': 'jiance',  # 数据库名称
    'charset': 'utf8mb4'  # 数据库字符集，支持存储多语言字符
}


# 获取主表中指定 name 的 id、max 和 min 值
def get_id_max_min(id_value):
    """
    根据主表中的 name 字段查询对应的 id、max 和 min 值。
    :param id_value: 主表中 name 字段的值
    :return: 查询到的 id、max 和 min 值，如果未找到则返回 None
    """
    connection = None
    try:
        # 建立数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # 查询主表中 name 对应的 id、max 和 min 值
        query = "SELECT id, max, min FROM main_table WHERE name = %s"
        cursor.execute(query, (id_value,))
        result = cursor.fetchone()  # 获取查询结果

        if result:
            # 如果查询到结果，解包返回 id、max 和 min 值
            id_value, max_value, min_value = result
            return id_value, max_value, min_value
        else:
            # 如果未查询到结果，打印提示信息并返回 None
            print(f"未找到 name 为 {id_value} 的记录")
            return None, None, None

    except Exception as e:
        # 捕获查询过程中发生的异常并打印错误信息
        print(f"查询 id、max 和 min 值时出错: {e}")
        return None, None, None
    finally:
        # 确保在查询结束后关闭数据库连接
        if connection:
            connection.close()


# 将检测结果保存到对应的子表
def saves(id_value, num, url, name):
    """
    将检测结果保存到对应的子表中。
    :param id_value: 主表中 name 字段的值
    :param num: 检测值
    :param url: 检测图片的 URL
    :param name: 检测时间或其他标识
    :return: 插入成功返回 1，失败返回 0
    """
    connection = None
    # 获取主表中对应的 id、max 和 min 值
    ids, max_value, min_value = get_id_max_min(id_value)
    table_name = f"sub_table_{ids}"  # 根据主表 id 构造子表名称

    # 如果 max 或 min 值为空，直接返回 0
    if max_value is None or min_value is None:
        return 0

    # 检测值在 max 和 min 范围内，标记为 "否"
    if float(max_value) > num > float(min_value):
        try:
            # 建立数据库连接
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()

            # 插入检测结果到子表，标记为 "否"
            insert_sql = f"""
                        INSERT INTO {table_name} (id, 时间, url, 检测值, 是否异常)
                        VALUES (%s, %s, %s, %s, '否')
                        """
            cursor.execute(insert_sql, (ids, name, url, num,))
            connection.commit()  # 提交事务
            return 1

        except Exception as e:
            # 捕获插入过程中发生的异常并打印错误信息
            print(f"插入子表时出错: {e}")
            return 0
    else:
        # 检测值不在 max 和 min 范围内，标记为 "是"
        try:
            # 建立数据库连接
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()

            # 插入检测结果到子表，标记为 "是"
            insert_sql = f"""
                                INSERT INTO {table_name} (id, 时间, url, 检测值, 是否异常)
                                VALUES (%s, %s, %s, %s, '是')
                                """
            cursor.execute(insert_sql, (ids, name, url, num,))
            connection.commit()  # 提交事务
            return 1

        except Exception as e:
            # 捕获插入过程中发生的异常并打印错误信息
            print(f"插入子表时出错: {e}")
            return 0


# 主程序入口，用于测试 saves 函数
if __name__ == '__main__':
    # 测试将检测值保存到子表
    saves(1, 0.7, 'sa', '552')
