import os
import re
from fastapi import HTTPException, Request, Response
from starlette.responses import FileResponse, StreamingResponse
from typing import Generator, Dict
from datetime import date, datetime, timedelta
import logging
from database import get_db_connection
from schemas import SleepRecord
from storage import StorageBackend, LocalStorage

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
                WHERE SUBSTR(r.timestamp, 1, 10) = ?
                GROUP BY r.id
                ORDER BY r.is_favorite DESC, r.timestamp DESC
            """
            params = (target_date.strftime('%Y-%m-%d'),)
            logging.info(f"Executing query: {query.strip()} with params: {params}")
            cursor.execute(query, params)
            
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

def get_audio_file_by_id(record_id: str, storage: StorageBackend, request: Request) -> Response:
    """
    根据记录 ID 从数据库获取音频文件流，支持 Range 请求。
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT audio_url FROM records WHERE id = ?"
            params = (record_id,)
            logging.info(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params)
            record = cursor.fetchone()
    except Exception as e:
        print(f"Error fetching record: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch record from database")

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    file_path_key = record['audio_url']

    # 如果是本地存储，直接使用 FileResponse，它原生支持 Range 请求
    if isinstance(storage, LocalStorage):
        full_path = os.path.join(storage.base_dir, file_path_key)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        return FileResponse(full_path, media_type="audio/wav", accept_ranges="bytes")

    # --- 对于 MinIO 等非本地存储，手动实现 Range 请求处理 ---
    
    file_size = storage.get_size(file_path_key)
    if file_size < 0:
        raise HTTPException(status_code=404, detail="Audio file not found in storage")

    range_header = request.headers.get('range')
    
    # 默认响应头
    headers = {
        "Content-Type": "audio/wav",
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Connection": "keep-alive",
    }
    
    start, end = 0, file_size - 1
    status_code = 200

    if range_header:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start_str, end_str = range_match.groups()
            start = int(start_str)
            end = int(end_str) if end_str else file_size - 1

            # 确保范围有效
            if start >= file_size or end >= file_size or start > end:
                 raise HTTPException(status_code=416, detail="Requested range not satisfiable")

            # 更新状态码和头部
            status_code = 206
            content_length = end - start + 1
            headers["Content-Length"] = str(content_length)
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    
    # 定义一个生成器来流式传输数据
    def stream_generator(offset: int, length: int) -> Generator[bytes, None, None]:
        stream = None
        try:
            stream = storage.get_stream(file_path_key, offset=offset, length=length)
            if stream is None:
                # 再次检查，以防万一
                raise HTTPException(status_code=404, detail="Failed to open audio stream")
            
            # MinIO 的 get_object 返回的是一个 urllib3.response.HTTPResponse 对象
            # 我们可以通过 stream() 方法迭代获取数据块
            for chunk in stream.stream(32 * 1024): # 32KB per chunk
                yield chunk
        finally:
            if hasattr(stream, 'close'):
                stream.close()

    # 根据状态码返回响应
    if status_code == 206:
        content_length = end - start + 1
        return StreamingResponse(
            stream_generator(start, content_length),
            status_code=status_code,
            headers=headers,
            media_type="audio/wav"
        )
    else: # 200
        return StreamingResponse(
            stream_generator(0, file_size),
            status_code=status_code,
            headers=headers,
            media_type="audio/wav"
        )

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
                    SUBSTR(timestamp, 1, 10) as record_date,
                    COUNT(id) as count,
                    AVG(duration) as avg_duration
                FROM records
                WHERE SUBSTR(timestamp, 1, 10) BETWEEN ? AND ?
                GROUP BY record_date
                ORDER BY record_date ASC
            """
            params_daily = (start_str, end_str)
            logging.info(f"Executing daily stats query with params: {params_daily}")
            cursor.execute(query_daily, params_daily)
            for row in cursor.fetchall():
                daily_stats.append(DailyStat(
                    date=row['record_date'],
                    count=row['count'],
                    avgDuration=round(row['avg_duration'], 1)
                ))
                
            # 2. Hourly Stats
            query_hourly = """
                SELECT
                    SUBSTR(timestamp, 12, 2) as hour_str,
                    COUNT(id) as count
                FROM records
                WHERE SUBSTR(timestamp, 1, 10) BETWEEN ? AND ?
                GROUP BY hour_str
                ORDER BY hour_str ASC
            """
            params_hourly = (start_str, end_str)
            logging.info(f"Executing hourly stats query with params: {params_hourly}")
            cursor.execute(query_hourly, params_hourly)
            
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
                WHERE SUBSTR(r.timestamp, 1, 10) BETWEEN ? AND ?
                GROUP BY t.name
                ORDER BY value DESC
            """
            params_tags = (start_str, end_str)
            logging.info(f"Executing tags stats query with params: {params_tags}")
            cursor.execute(query_tags, params_tags)
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
                    SUBSTR(timestamp, 1, 10) as record_date,
                    COUNT(id) as total_records,
                    SUM(CASE WHEN is_favorite = 1 THEN 1 ELSE 0 END) as favorite_records
                FROM records
                WHERE SUBSTR(timestamp, 1, 7) = ?
                GROUP BY record_date
            """
            year_month_str = f"{year}-{month:02d}"
            params_monthly = (year_month_str,)
            logging.info(f"Executing monthly activity query with params: {params_monthly}")
            cursor.execute(query, params_monthly)
            
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
            now = datetime.now().isoformat()
            
            query_fav = "UPDATE records SET is_favorite = ?, updated_at = ? WHERE id = ?"
            params_fav = (favorite_value, now, record_id)
            logging.info(f"Executing favorite update query with params: {params_fav}")
            cursor.execute(query_fav, params_fav)
            conn.commit()
            return cursor.rowcount > 0 # 如果更新了一行或多行，则返回 True
    except Exception as e:
        print(f"Error updating favorite status for record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not update favorite status")

def delete_record(record_id: str, storage: StorageBackend) -> bool:
    """
    删除指定的梦话记录及对应的音频文件。
    """
    # 1. 获取记录信息以得到 audio_url
    record = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT audio_url FROM records WHERE id = ?"
            cursor.execute(query, (record_id,))
            record = cursor.fetchone()
    except Exception as e:
        print(f"Error fetching record for deletion: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch record info")

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    audio_url = record['audio_url']

    # 2. 从存储中删除文件
    # 即使数据库删除失败，我们也尝试删除文件，或者反过来？
    # 通常应该先删除数据库记录，再删除文件，或者使用事务。
    # 这里我们先尝试从数据库删除，如果成功再删除文件。
    # 因为文件删除不可逆且较难回滚，而数据库操作在事务中。
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 删除标签关联
            cursor.execute("DELETE FROM record_tags WHERE record_id = ?", (record_id,))
            
            # 删除记录
            cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
            
            if cursor.rowcount == 0:
                # 理论上前面查到了，这里不应该发生，除非并发删除
                raise HTTPException(status_code=404, detail="Record not found during deletion")
            
            conn.commit()
    except Exception as e:
        print(f"Error deleting record from database: {e}")
        raise HTTPException(status_code=500, detail="Could not delete record from database")

    # 3. 删除文件
    # 如果文件删除失败，我们只记录日志，不回滚数据库，因为记录已经不存在了
    try:
        storage.delete(audio_url)
    except Exception as e:
        logging.error(f"Failed to delete audio file {audio_url} for record {record_id}: {e}")
        # 不抛出异常，因为记录已经删除了

    return True
