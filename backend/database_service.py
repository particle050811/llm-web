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
            object_name TEXT,
            school TEXT,
            method TEXT,
            phone TEXT,
            time TEXT,
            transcription_text TEXT,
            submission_timestamp TEXT,
            PRIMARY KEY (object_name, submission_timestamp)
        )
    ''')
    conn.commit()
    conn.close()

def save_report_data(report_data):
    """
    将举报数据保存到 SQLite 数据库中，以 object_name 和 submission_timestamp 为复合主键。

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
        return True, f"数据已成功保存或更新，复合主键为: {object_name}, {submission_timestamp}"
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False, f"数据库操作失败: {e}"

def get_all_reports():
    """获取所有举报数据
    
    Returns:
        list: 举报数据列表，每个元素是一个字典
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # 使返回字典格式
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT r.object_name, r.school, r.method, r.phone, r.time, r.transcription_text, r.submission_timestamp
            FROM reports r
            INNER JOIN (
                SELECT object_name, MAX(submission_timestamp) as max_timestamp
                FROM reports
                GROUP BY object_name
            ) latest ON r.object_name = latest.object_name AND r.submission_timestamp = latest.max_timestamp
            ORDER BY r.submission_timestamp DESC
        ''')
        reports = [dict(row) for row in cursor.fetchall()]
        return reports
    except sqlite3.Error as e:
        print(f"数据库查询错误: {e}")
        return []
    finally:
        conn.close()

def get_submission_timestamps(object_name):
    """获取指定 object_name 的所有 submission_timestamp
    
    Args:
        object_name (str): 报告的对象名称
        
    Returns:
        list: 时间戳字符串列表，按降序排列
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT submission_timestamp
            FROM reports
            WHERE object_name = ?
            ORDER BY submission_timestamp DESC
        ''', (object_name,))
        timestamps = [row[0] for row in cursor.fetchall()]
        return timestamps
    except sqlite3.Error as e:
        print(f"数据库查询错误 (get_submission_timestamps): {e}")
        return []
    finally:
        conn.close()

def get_report_by_timestamp(object_name, submission_timestamp=None):
    """根据 object_name 和 submission_timestamp 获取报告详情。
       如果 submission_timestamp 为空或未提供，则返回最新的报告。

    Args:
        object_name (str): 报告的对象名称
        submission_timestamp (str, optional): 报告的提交时间戳。默认为 None，表示获取最新版本。

    Returns:
        dict: 包含报告详情的字典，如果未找到则返回 None
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        if submission_timestamp:
            # 如果提供了时间戳，查询特定版本
            cursor.execute('''
                SELECT *
                FROM reports
                WHERE object_name = ? AND submission_timestamp = ?
            ''', (object_name, submission_timestamp))
        else:
            # 如果未提供时间戳，查询最新版本
            cursor.execute('''
                SELECT *
                FROM reports
                WHERE object_name = ?
                ORDER BY submission_timestamp DESC
                LIMIT 1
            ''', (object_name,))

        report = cursor.fetchone()
        return dict(report) if report else None
    except sqlite3.Error as e:
        print(f"数据库查询错误 (get_report_by_timestamp): {e}")
        return None
    finally:
        conn.close()

# 应用启动时初始化数据库
init_db()