# 仪表检测管理系统

本项目是一套基于深度学习的仪表自动检测与管理系统，集成了图片采集、仪表识别、渗水检测、数据库管理、Web 可视化等功能，适用于工业现场的自动化检测与数据管理。

## 功能简介

- **图片采集与处理**：通过 socket 或文件夹接收图片，自动分类检测仪表类型（机械表/数字表/渗水）。
- **仪表识别**：基于 YOLO 与 OCR 实现仪表读数自动识别与异常判断。
- **渗水检测**：支持渗水异常检测与报告生成。
- **数据库管理**：自动维护主表、子表、渗水报告表等，支持自动建表。
- **Web 管理界面**：基于 FastAPI + Vue3，支持主表管理、检测结果查询、异常报警、渗水报告等。
- **远程导航**：支持通过 SSH 发送坐标到机器人进行自动导航。

## 目录结构

```
.
├── main.py                # 主程序入口，负责多线程调度与图片监控
├── classification_detection.py  # 分类检测主逻辑
├── jixiebiao.py           # 机械表检测与读数
├── shuzibiao.py           # 数字表检测与读数
├── sz_jiance.py           # 渗水检测
├── save_sql.py            # 检测结果保存到数据库
├── SQL_auto.py            # 数据库自动建表与监控
├── fastweb.py             # FastAPI Web 后端
├── static/home.html       # 前端页面（Vue3）
├── soc.py                 # 图片接收 socket 服务
├── xj.py                  # 坐标获取与 SSH 远程导航
├── automaticEntry.py      # 二维码批量入库工具
├── model/                 # 训练好的模型文件
├── imageod/               # 图片输入目录
├── old_tmp/               # 监控图片目录
├── jieguo/                # 检测结果图片输出目录
├── tmp/                   # 临时图片目录
└── ...
```

## 依赖环境

- Python 3.8+
- OpenCV
- PaddleOCR
- ultralytics (YOLO)
- pymysql
- paramiko
- fastapi
- uvicorn
- watchdog
- pillow
- pyzbar
- schedule

安装依赖（推荐使用虚拟环境）：

```bash
pip install -r requirements.txt
```

## 数据库说明

- 使用 MySQL，需提前创建 `jiance` 数据库，账号密码请在各 py 文件 `db_config` 处配置。
- 程序会自动建表（主表、子表、渗水报告表、坐标表）。

## 运行方式

1. 启动 MySQL 数据库，确保账号密码正确。
2. 启动主程序：

```bash
python main.py
```

3. 访问 Web 管理界面：

```
http://localhost:8000/
```

## 主要流程

- 图片通过 socket 或文件夹写入 `old_tmp/`，被自动检测、识别、结果入库。
- Web 前端可进行主表管理、检测结果查询、异常报警查看、渗水报告管理等。
- 支持批量二维码图片自动入库（`automaticEntry.py`）。

## 贡献与许可

欢迎交流与二次开发，代码仅供学习与科研用途。

