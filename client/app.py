import asyncio
import logging
import uvicorn
import websockets
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from recorder import Recorder
from log import init_log

init_log()
logger = logging.getLogger(__name__)

class WebsocketManager:
    """
    管理与 VAD 服务器的 WebSocket 连接。
    """
    def __init__(self):
        self.is_connected = False  # 连接状态标志
        self._task: asyncio.Task = None  # 用于发送音频数据的后台任务

    async def connect(self, recorder: Recorder, server_url: str):
        """
        连接到 VAD 服务器，并启动一个后台任务来发送音频数据。
        :param recorder: 录音机实例
        :param server_url: VAD 服务器的 WebSocket URL
        """
        if self.is_connected:
            logger.warning("已经连接到服务器。")
            return
        
        try:
            # 建立 WebSocket 连接
            websocket = await websockets.connect(server_url)
            self.is_connected = True
            # 开始录音
            recorder.start()

            async def sender(ws):
                """
                这是一个后台任务，它从录音机的队列中获取音频数据，
                并通过 WebSocket 发送到服务器。
                """
                while self.is_connected:
                    try:
                        audio_data = await recorder.q.get()
                        await ws.send(audio_data.tobytes())
                    except asyncio.CancelledError:
                        # 当任务被取消时，退出循环
                        break
                # 任务结束时，停止录音并关闭 WebSocket 连接
                recorder.stop()
                await ws.close()

            # 创建并启动后台发送任务
            self._task = asyncio.create_task(sender(websocket))
            logger.info(f"已连接到 VAD 服务器: {server_url}")
        except Exception as e:
            logger.error(f"连接 VAD 服务器失败: {e}")
            self.is_connected = False

    async def disconnect(self):
        """断开与 VAD 服务器的连接，并停止后台任务。"""
        if not self.is_connected:
            logger.warning("未连接到服务器。")
            return

        self.is_connected = False
        if self._task:
            # 取消后台任务并等待其完成
            self._task.cancel()
            await self._task
        
        logger.info("已从 VAD 服务器断开。")

# 全局 WebSocket 管理器和录音机实例
websocket_manager = WebsocketManager()
recorder: Recorder = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 的生命周期事件，在应用启动时初始化录音机。"""
    global recorder
    recorder = Recorder()
    yield
    # 在应用关闭时，确保断开 WebSocket 连接
    if websocket_manager.is_connected:
        await websocket_manager.disconnect()

app = FastAPI(lifespan=lifespan)

@app.post("/ws/connect")
async def ws_connect(server_url: str = "ws://127.0.0.1:8569/vad"):
    """HTTP 端点，用于触发 WebSocket 连接。"""
    if not recorder:
        raise HTTPException(status_code=500, detail="录音机未初始化")
    
    await websocket_manager.connect(recorder, server_url)
    return {"status": "正在连接"}

@app.post("/ws/disconnect")
async def ws_disconnect():
    """HTTP 端点，用于断开 WebSocket 连接。"""
    await websocket_manager.disconnect()
    return {"status": "正在断开"}

if __name__ == "__main__":
    # 客户端运行在不同的端口以避免与服务器冲突
    uvicorn.run("app:app", host="0.0.0.0", port=8570, reload=True)
