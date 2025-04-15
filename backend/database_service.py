# backend/database_service.py
import sqlite3
import os
from datetime import datetime

# 获取当前脚本文件所在的目录
script_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(script_dir, 'report_database.db')

def init_db():
    """初始化数据库，创建表（如果不存在）"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            object_name TEXT PRIMARY KEY,
            school TEXT,
            method TEXT,
            phone TEXT,
            time TEXT,
            transcription_text TEXT,
            submission_timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_report_data(report_data):
    """
    将举报数据保存到 SQLite 数据库中，以 object_name 为主键。

    Args:
        report_data (dict): 包含举报信息的字典，必须包含 'object_name'。

    Returns:
        tuple: (bool, str) 表示操作是否成功和相应的消息。
    """
    if 'object_name' not in report_data:
        return False, "缺少 'object_name' 字段"

    object_name = report_data['object_name']
    school = report_data.get("school")
    method = report_data.get("method")
    phone = report_data.get("phone")
    time = report_data.get("time")
    transcription_text = report_data.get("transcription_text")
    submission_timestamp = datetime.now().isoformat() # 添加提交时间戳

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # 使用 INSERT OR REPLACE 来插入或更新记录
        cursor.execute('''
            INSERT OR REPLACE INTO reports (object_name, school, method, phone, time, transcription_text, submission_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (object_name, school, method, phone, time, transcription_text, submission_timestamp))
        conn.commit()
        conn.close()
        return True, f"数据已成功保存或更新，主键为: {object_name}"
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False, f"数据库操作失败: {e}"

# 应用启动时初始化数据库
init_db()