from contextlib import asynccontextmanager
import logging
import uvicorn
import yaml
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from log import init_log
from vad.engine import VadEngine
from stt import get_stt_engine, STTEngine

init_log()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 的生命周期事件，在应用启动时执行。"""
    await startup_event()
    yield


app = FastAPI(lifespan=lifespan)

# 全局 VAD 和 STT 引擎实例
vad_engine: VadEngine = None
stt_engine: STTEngine = None


async def startup_event():
    """在应用启动时加载 VAD 和 STT 模型。"""
    global vad_engine, stt_engine
    config_path = os.path.join(os.path.dirname(__file__), '.config.yaml')
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    
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

    async def on_speech_end(speech_data: bytes):
        """当检测到语音片段结束时的回调函数。"""
        logger.info(f"检测到语音片段，长度为 {len(speech_data)} 字节。")
        # 在实际应用中，你可能会将此音频数据发送到语音转文本服务
        # 或者将其回传给客户端进行处理。
        # await websocket.send_bytes(speech_data)

    # 为当前 WebSocket 连接创建一个 VadWrapper 实例
    vad_wrapper = vad_engine.get_vad_wrapper(on_speech_end, stt_engine)

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
    except Exception as e:
        # 发生其他异常时，同样重置 VAD 状态
        vad_wrapper.reset()
        logger.error(f"WebSocket 发生错误: {e}")


if __name__ == "__main__":
    # FIXME: reload 会监听 logs 文件
    uvicorn.run(
        "app:app", host="0.0.0.0", port=8569, reload=True, reload_excludes=["logs"]
    )
