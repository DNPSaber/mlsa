import pymysql
import time

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
            return cursor.fetchall()
    except Exception as e:
        print(f"执行查询时出错: {e}")
        return None
    finally:
        if connection:
            connection.close()


def get_main_table_count():
    result = execute_query("SELECT COUNT(*) FROM main_table")
    return result[0][0] if result else 0


def ensure_main_table_exists():
    table_exists_query = """
                         SELECT COUNT(*)
                         FROM information_schema.tables
                         WHERE table_schema = DATABASE()
                           AND table_name = 'main_table' \
                         """
    create_table_query = """
                         CREATE TABLE main_table
                         (
                             id   INT AUTO_INCREMENT PRIMARY KEY,
                             name VARCHAR(255) NOT NULL,
                             x    VARCHAR(255) NOT NULL,
                             y    VARCHAR(255) NOT NULL,
                             yaw    VARCHAR(255) NOT NULL,
                             max  VARCHAR(255) NOT NULL,
                             min  VARCHAR(255) NOT NULL
                         ) \
                         """
    result = execute_query(table_exists_query)
    if result and result[0][0] == 0:
        execute_query(create_table_query)
        print("主表 main_table 创建成功")

    
def ensure_sub_tables_exist():
    ids = execute_query("SELECT id FROM main_table")
    if not ids:
        return
    for (id_value,) in ids:
        table_name = f"sub_table_{id_value}"
        table_exists_query = """
                             SELECT COUNT(*)
                             FROM information_schema.tables
                             WHERE table_schema = DATABASE()
                               AND table_name = %s \
                             """
        create_table_query = f"""
                        CREATE TABLE {table_name} (
                            时间 VARCHAR(255) NOT NULL,
                            url VARCHAR(255) NOT NULL,
                            检测值 VARCHAR(255) NOT NULL,
                            是否异常 VARCHAR(255) NOT NULL,
                            id INT NOT NULL,
                            FOREIGN KEY (id) REFERENCES main_table(id)
                        )
                    """
        result = execute_query(table_exists_query, (table_name,))
        if result and result[0][0] == 0:
            execute_query(create_table_query)
            print(f"子表 {table_name} 创建成功")


def monitor_database():
    ensure_main_table_exists()
    last_count = get_main_table_count()

    try:
        while True:
            current_count = get_main_table_count()
            if current_count > last_count:
                print("检测到主表 id 增加，开始创建子表...")
                ensure_sub_tables_exist()   
                last_count = current_count
            time.sleep(5)
    except KeyboardInterrupt:
        print("监控已停止")


if __name__ == "__main__":
    print("开始监控数据库...")
    monitor_database()
