import sqlite3
import logging
import os
from datetime import datetime
from typing import List
import uuid
from schemas import SleepRecordCreate

logger = logging.getLogger(__name__)

DB_FILE = os.path.join(os.path.dirname(__file__), 'data', 'dream_talker.db')

def get_db_connection():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库，创建表结构"""
    logger.info("Initializing database...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 创建 records 表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                duration INTEGER NOT NULL,
                audio_url TEXT NOT NULL,
                transcription TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.0,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                image_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 创建 tags 表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            """)

            # 创建 record_tags 关联表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS record_tags (
                record_id TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (record_id, tag_id),
                FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            """)
            
            # 创建 keyword_stats 表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyword_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                value INTEGER NOT NULL,
                category TEXT NOT NULL,
                record_id TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
            );
            """)
            
            conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def add_record(record_data: SleepRecordCreate):
    """
    将一条新的语音记录添加到数据库中。
    
    Args:
        record_data: SleepRecordCreate 实例
    """
    now = datetime.utcnow().isoformat()
    record_id = str(uuid.uuid4())

    sql_insert_record = """
    INSERT INTO records (id, timestamp, duration, audio_url, transcription, confidence, is_favorite, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    
    record_tuple = (
        record_id,
        record_data.timestamp,
        record_data.duration,
        record_data.audio_url,
        record_data.transcription,
        record_data.confidence,
        0,  # is_favorite 默认为 0
        now,
        now
    )
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 插入主记录
            cursor.execute(sql_insert_record, record_tuple)
            
            # 处理标签
            tags = record_data.tags
            for tag_name in tags:
                # 查找或创建 tag
                cursor.execute("SELECT id FROM tags WHERE name = ?;", (tag_name,))
                tag = cursor.fetchone()
                if tag:
                    tag_id = tag['id']
                else:
                    cursor.execute("INSERT INTO tags (name) VALUES (?);", (tag_name,))
                    tag_id = cursor.lastrowid
                
                # 插入关联表
                cursor.execute("INSERT INTO record_tags (record_id, tag_id) VALUES (?, ?);", (record_id, tag_id))
            
            conn.commit()
            logger.info(f"Successfully added record with ID: {record_id}")
            return record_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add record: {e}")
        return None

if __name__ == '__main__':
    # 作为脚本运行时，初始化数据库
    init_log_path = os.path.join(os.path.dirname(__file__), 'log.py')
    if os.path.exists(init_log_path):
        from log import init_log
        init_log()
    init_db()
    # 示例: 添加一条记录
    # add_record({
    #     "timestamp": datetime.utcnow().isoformat(),
    #     "duration": 5,
    #     "audio_url": "/path/to/audio.wav",
    #     "transcription": "这是一段测试。",
    #     "confidence": 0.98,
    #     "tags": ["测试", "清晰"]
    # })
