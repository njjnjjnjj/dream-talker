from contextlib import asynccontextmanager
import logging
import uvicorn
import yaml
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from datetime import date, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel # 导入 BaseModel 用于请求体

from log import init_log
from vad.engine import VadEngine
from stt import get_stt_engine, STTEngine
from database import init_db, add_record
from schemas import MonthlyActivity, SleepRecordCreate, SleepRecord, StatisticsResponse
from records import get_records_by_date, get_audio_file_by_id, get_monthly_record_activity, update_record_favorite_status, get_statistics
from storage import get_storage_backend, StorageBackend

init_log()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 的生命周期事件，在应用启动时执行。"""
    init_db()
    await startup_event()
    yield


app = FastAPI(lifespan=lifespan)

# 全局 VAD, STT 和 Storage 实例
vad_engine: VadEngine = None
stt_engine: STTEngine = None
storage_backend: StorageBackend = None


async def startup_event():
    """在应用启动时加载 VAD 和 STT 模型。"""
    global vad_engine, stt_engine, storage_backend
    config_path = os.path.join(os.path.dirname(__file__), '.config.yaml')
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    
    # 初始化存储后端
    storage_config = config.get('storage', {})
    storage_backend = get_storage_backend(storage_config)
    logger.info(f"存储后端已初始化: {storage_config.get('type', 'local')}")

    # 初始化 VAD 引擎
    vad_config = config.get('vad', {})
    vad_engine = VadEngine(vad_config=vad_config)

    # 初始化 STT 引擎
    stt_config = config.get('stt', {})
    stt_engine = get_stt_engine(stt_config)


@app.websocket("/vad")
async def websocket_binary(websocket: WebSocket):
    """处理 WebSocket 二进制音频流的端点。"""
    await websocket.accept()
    logger.info("WebSocket 连接已接受。")

    async def on_speech_end(record_data: SleepRecordCreate):
        """当检测到语音片段结束时的回调函数，将数据保存到数据库。"""
        logger.info(f"接收到新的语音记录: {record_data}")
        add_record(record_data)

    # 为当前 WebSocket 连接创建一个 VadWrapper 实例
    vad_wrapper = vad_engine.get_vad_wrapper(on_speech_end, stt_engine, storage_backend)

    try:
        # 持续接收来自客户端的音频数据
        while True:
            data: bytes = await websocket.receive_bytes()
            # 将音频数据喂给 VAD 处理器
            await vad_wrapper.process(data)
    except WebSocketDisconnect:
        # 当客户端断开连接时，重置 VAD 状态
        vad_wrapper.reset()
        logger.info("WebSocket 连接已断开。")
    except Exception:
        # 发生其他异常时，同样重置 VAD 状态
        vad_wrapper.reset()
        logger.error("WebSocket 发生错误", exc_info=True)


@app.get("/api/records", response_model=List[SleepRecord])
async def read_records_by_date(date: date):
    """
    获取指定日期的梦话记录。
    """
    return get_records_by_date(date)


@app.get("/api/records/activity", response_model=MonthlyActivity)
async def read_record_activity(year: int, month: int):
    """
    获取指定月份每日的梦话记录数量。
    """
    return get_monthly_record_activity(year, month)


@app.get("/api/statistics", response_model=StatisticsResponse)
async def read_statistics(start_date: Optional[date] = None, end_date: Optional[date] = None, days: Optional[int] = None):
    """
    获取统计数据。
    """
    if days is not None and start_date is None and end_date is None:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
    return get_statistics(start_date, end_date)


class UpdateFavoriteRequest(BaseModel):
    is_favorite: bool

@app.put("/api/records/{record_id}/favorite")
async def update_favorite_status(record_id: str, request: UpdateFavoriteRequest):
    """
    更新记录的收藏状态。
    """
    success = update_record_favorite_status(record_id, request.is_favorite)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found or update failed")
    return {"status": "success", "message": "Favorite status updated"}


@app.get("/api/audio/{record_id}")
async def stream_audio_file(record_id: str):
    """
    以文件流形式提供音频文件。
    """
    return get_audio_file_by_id(record_id, storage_backend)


if __name__ == "__main__":
    # FIXME: reload 会监听 logs 文件
    uvicorn.run(
        "app:app", host="0.0.0.0", port=8569, reload=True, reload_excludes=["logs"]
    )
