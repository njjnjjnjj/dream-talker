import os
from fastapi import HTTPException
from starlette.responses import FileResponse
from datetime import date, datetime
from database import get_db_connection
from schemas import SleepRecord

RECORDS_BASE_DIR = os.path.join(os.path.dirname(__file__), "data", "records")

def get_records_by_date(target_date: date) -> list[SleepRecord]:
    """
    根据指定日期从数据库获取梦话记录。
    """
    records = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT r.id, r.timestamp, r.duration, r.audio_url, r.transcription, r.confidence, r.is_favorite, GROUP_CONCAT(t.name) as tags
                FROM records r
                LEFT JOIN record_tags rt ON r.id = rt.record_id
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE r.timestamp LIKE ?
                GROUP BY r.id
                ORDER BY r.timestamp DESC
            """
            cursor.execute(query, (f"{target_date.strftime('%Y-%m-%d')}%",))
            
            for row in cursor.fetchall():
                # 将数据库行转换为 SleepRecord 对象
                tags = row['tags'].split(',') if row['tags'] else []
                record = SleepRecord(
                    id=row['id'],
                    timestamp=row['timestamp'],
                    duration=row['duration'],
                    audio_url=row['audio_url'],
                    transcription=row['transcription'],
                    confidence=row['confidence'],
                    is_favorite=bool(row['is_favorite']), # 将数据库的 0/1 转换为布尔值
                    tags=tags
                )
                records.append(record)
    except Exception as e:
        # 在实际应用中应该记录日志
        print(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch records from database")

    return records

def get_audio_file_by_id(record_id: str) -> FileResponse:
    """
    根据记录 ID 从数据库获取音频文件流。
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT audio_url FROM records WHERE id = ?", (record_id,))
            record = cursor.fetchone()
    except Exception as e:
        print(f"Error fetching record: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch record from database")

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    # audio_url is a relative path, we need to join it with the base dir
    file_path = os.path.join(RECORDS_BASE_DIR, record['audio_url'])
    
    print(f"Serving audio file from path: {file_path}")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(file_path, media_type="audio/wav")

from schemas import SleepRecord, MonthlyActivity

def get_monthly_record_activity(year: int, month: int) -> MonthlyActivity:
    """
    获取指定月份每日的梦话记录数量。
    """
    activity_data: Dict[str, int] = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    strftime('%Y-%m-%d', timestamp) as record_date,
                    COUNT(id) as record_count
                FROM records
                WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?
                GROUP BY record_date
            """
            month_str = str(month).zfill(2)
            cursor.execute(query, (str(year), month_str))
            
            for row in cursor.fetchall():
                activity_data[row['record_date']] = row['record_count']
    except Exception as e:
        print(f"Error fetching monthly activity: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch monthly activity")

    return MonthlyActivity(activity=activity_data)

def update_record_favorite_status(record_id: str, is_favorite: bool) -> bool:
    """
    更新指定记录的收藏状态。
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # SQLite 存储布尔值为 0 或 1
            favorite_value = 1 if is_favorite else 0
            now = datetime.utcnow().isoformat() # 导入 datetime
            
            cursor.execute(
                "UPDATE records SET is_favorite = ?, updated_at = ? WHERE id = ?",
                (favorite_value, now, record_id)
            )
            conn.commit()
            return cursor.rowcount > 0 # 如果更新了一行或多行，则返回 True
    except Exception as e:
        print(f"Error updating favorite status for record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not update favorite status")
