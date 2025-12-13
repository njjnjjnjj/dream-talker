import os
from fastapi import HTTPException
from starlette.responses import FileResponse, StreamingResponse
from datetime import date, datetime
from database import get_db_connection
from schemas import SleepRecord
from storage import StorageBackend, LocalStorage

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
                ORDER BY r.is_favorite DESC, r.timestamp DESC
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

def get_audio_file_by_id(record_id: str, storage: StorageBackend) -> StreamingResponse | FileResponse:
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

    file_path_key = record['audio_url']
    
    # 如果是本地存储，并且确实是本地文件，我们可以使用高效的 FileResponse
    # 但为了统一接口，如果 StorageBackend 提供了本地路径，我们可以优化
    if isinstance(storage, LocalStorage):
        full_path = os.path.join(storage.base_dir, file_path_key)
        if not os.path.exists(full_path):
             raise HTTPException(status_code=404, detail="Audio file not found")
        return FileResponse(full_path, media_type="audio/wav")

    # 对于 MinIO 或其他后端，使用流式响应
    stream = storage.get_stream(file_path_key)
    if stream is None:
        raise HTTPException(status_code=404, detail="Audio file not found in storage")

    return StreamingResponse(stream, media_type="audio/wav")

from schemas import SleepRecord, MonthlyActivity, DailyActivitySummary, StatisticsResponse, DailyStat, HourlyStat, TagStat, KeywordStat

def get_statistics(start_date: date = None, end_date: date = None) -> StatisticsResponse:
    """
    获取指定日期范围内的统计数据。
    """
    daily_stats = []
    hourly_stats = []
    tag_stats = []
    
    # 默认最近 7 天
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    # 为了包含 end_date 的全天，我们需要比较日期部分
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Daily Stats
            query_daily = """
                SELECT
                    strftime('%Y-%m-%d', timestamp) as record_date,
                    COUNT(id) as count,
                    AVG(duration) as avg_duration
                FROM records
                WHERE strftime('%Y-%m-%d', timestamp) BETWEEN ? AND ?
                GROUP BY record_date
                ORDER BY record_date ASC
            """
            cursor.execute(query_daily, (start_str, end_str))
            for row in cursor.fetchall():
                daily_stats.append(DailyStat(
                    date=row['record_date'],
                    count=row['count'],
                    avgDuration=round(row['avg_duration'], 1)
                ))
                
            # 2. Hourly Stats
            query_hourly = """
                SELECT
                    strftime('%H', timestamp) as hour_str,
                    COUNT(id) as count
                FROM records
                WHERE strftime('%Y-%m-%d', timestamp) BETWEEN ? AND ?
                GROUP BY hour_str
                ORDER BY hour_str ASC
            """
            cursor.execute(query_hourly, (start_str, end_str))
            
            hourly_map = {f"{h:02d}": 0 for h in range(24)}
            for row in cursor.fetchall():
                hourly_map[row['hour_str']] = row['count']
            
            for h in sorted(hourly_map.keys()):
                hourly_stats.append(HourlyStat(
                    hour=f"{h}:00",
                    count=hourly_map[h]
                ))
            
            # 3. Tag Stats
            query_tags = """
                SELECT
                    t.name,
                    COUNT(rt.record_id) as value
                FROM tags t
                JOIN record_tags rt ON t.id = rt.tag_id
                JOIN records r ON rt.record_id = r.id
                WHERE strftime('%Y-%m-%d', r.timestamp) BETWEEN ? AND ?
                GROUP BY t.name
                ORDER BY value DESC
            """
            cursor.execute(query_tags, (start_str, end_str))
            for row in cursor.fetchall():
                tag_stats.append(TagStat(
                    name=row['name'],
                    value=row['value']
                ))

    except Exception as e:
        print(f"Error fetching statistics: {e}")
        # Return empty on error or raise?
        raise HTTPException(status_code=500, detail="Could not fetch statistics")

    return StatisticsResponse(
        dailyStats=daily_stats,
        hourlyStats=hourly_stats,
        tagStats=tag_stats,
        keywordData=[] # 暂时不实现 Keyword Heatmap
    )

def get_monthly_record_activity(year: int, month: int) -> MonthlyActivity:
    """
    获取指定月份每日的梦话记录数量。
    """
    activity_data: Dict[str, DailyActivitySummary] = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    strftime('%Y-%m-%d', timestamp) as record_date,
                    COUNT(id) as total_records,
                    SUM(CASE WHEN is_favorite = 1 THEN 1 ELSE 0 END) as favorite_records
                FROM records
                WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?
                GROUP BY record_date
            """
            month_str = str(month).zfill(2)
            cursor.execute(query, (str(year), month_str))
            
            for row in cursor.fetchall():
                activity_data[row['record_date']] = DailyActivitySummary(
                    total_records=row['total_records'],
                    favorite_records=row['favorite_records']
                )
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
