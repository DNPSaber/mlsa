from fastapi import FastAPI,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import pymysql

app = FastAPI()
app.mount("/jieguo", StaticFiles(directory="jieguo"), name="jieguo")

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '8507181ZZZzzz',
    'database': 'jiance',
    'charset': 'utf8mb4'
}


# 主表模型
class MainTable(BaseModel):
    name: str
    x: str
    y: str
    yaw: str
    max: str
    min: str


class MainTableUpdate(MainTable):
    id: int


# 渗水检测两点坐标模型
class SzPoint(BaseModel):
    start: str
    end: str


@app.get("/")
def read_root():
    return FileResponse("static/home.html")


# 获取主表所有数据
@app.get("/api/main")
def get_main():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, x, y, yaw, max, min FROM main_table")
        rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "x": r[2], "y": r[3], "yaw": r[4], "max": r[5], "min": r[6]} for r in rows
    ]


# 新增主表
@app.post("/api/main")
def add_main(item: MainTable):
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO main_table (name, x, y, yaw, max, min) VALUES (%s, %s, %s, %s, %s, %s)",
            (item.name, item.x, item.y, item.yaw, item.max, item.min)
        )
        conn.commit()
    conn.close()
    return {"msg": "ok"}


# 修改主表
@app.put("/api/main/{id}")
def update_main(id: int, item: MainTable):
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE main_table SET name=%s, x=%s, y=%s, yaw=%s, max=%s, min=%s WHERE id=%s",
            (item.name, item.x, item.y, item.yaw, item.max, item.min, id)
        )
        conn.commit()
    conn.close()
    return {"msg": "ok"}


# 删除主表
@app.delete("/api/main/{id}")
def delete_main(id: int):
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM main_table WHERE id=%s", (id,))
        conn.commit()
    conn.close()
    return {"msg": "ok"}


# 检测结果查询（按主表id或name）
@app.get("/api/results")
def get_results(key: str = Query("")):
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        # 先查主表id
        if key.isdigit():
            cur.execute("SELECT id FROM main_table WHERE id=%s", (key,))
        else:
            cur.execute("SELECT id FROM main_table WHERE name=%s", (key,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return []
        id_value = row[0]
        table_name = f"sub_table_{id_value}"
        try:
            cur.execute(f"SELECT 时间, url, 检测值, 是否异常 FROM {table_name} ORDER BY 时间 DESC LIMIT 50")
            rows = cur.fetchall()
        except Exception:
            rows = []
    conn.close()
    return [
        {"时间": r[0], "url": r[1], "检测值": r[2], "是否异常": r[3]} for r in rows
    ]


# 异常报警信息
@app.get("/api/alarms")
def get_alarms():
    conn = pymysql.connect(**DB_CONFIG)
    alarms = []
    with conn.cursor() as cur:
        # 主表异常
        cur.execute("SELECT id FROM main_table")
        ids = [r[0] for r in cur.fetchall()]
        for id_value in ids:
            table_name = f"sub_table_{id_value}"
            try:
                cur.execute(
                    f"SELECT 时间, url, 检测值, id FROM {table_name} WHERE 是否异常='是' ORDER BY 时间 DESC LIMIT 10")
                rows = cur.fetchall()
                for r in rows:
                    alarms.append({"时间": r[0], "url": r[1], "检测值": r[2], "id": r[3], "类型": "仪表异常"})
            except Exception:
                continue
        # 渗水异常
        try:
            cur.execute("SELECT 时间, url, 检测结果, 坐标 FROM sz_report WHERE 检测结果='异常' ORDER BY 时间 DESC LIMIT 10")
            rows = cur.fetchall()
            for r in rows:
                alarms.append({"时间": r[0], "url": r[1], "检测结果": r[2], "坐标": r[3], "类型": "渗水异常"})
        except Exception:
            pass
    conn.close()
    # 按时间倒序
    alarms.sort(key=lambda x: x["时间"], reverse=True)
    return alarms[:50]


# 渗水检测报告API
@app.get("/api/sz_reports")
def get_sz_reports():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 时间, 坐标, 检测结果, url FROM sz_report ORDER BY 时间 DESC LIMIT 100
        """)
        rows = cur.fetchall()
    conn.close()
    return [
        {"时间": r[0], "坐标": r[1], "检测结果": r[2], "url": r[3]} for r in rows
    ]


# 渗水检测两点坐标增查API
@app.get("/api/sz_points")
def get_sz_points():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SELECT id, start, end FROM sz_points ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "start": row[1], "end": row[2]}
    else:
        return {"id": None, "start": "", "end": ""}


@app.post("/api/sz_points")
def set_sz_points(item: SzPoint):
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO sz_points (start, end) VALUES (%s, %s)", (item.start, item.end))
        conn.commit()
    conn.close()
    return {"msg": "ok"}


def run():
    uvicorn.run(app)


if __name__ == "__main__":
    run()
