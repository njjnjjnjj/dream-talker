import asyncio
import logging
import uvicorn
import websockets
import yaml
import os
import numpy as np
import resampy
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from recorder import Recorder
from log import init_log

init_log()
logger = logging.getLogger(__name__)

# 全局配置变量
config = {}

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), ".config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            global config
            config = yaml.safe_load(f)
        logger.info(f"配置文件已加载: {config}")
    else:
        logger.warning(f"配置文件未找到: {config_path}")

class WebsocketManager:
    """
    管理与 VAD 服务器的 WebSocket 连接。
    包括自动重连机制。
    """
    def __init__(self):
        self.is_running = False  # 标记是否应该保持运行（包括重连）
        self._manage_task: asyncio.Task = None  # 连接管理任务
        self.server_url = ""
        self.recorder = None
        self.MAX_RECONNECT_ATTEMPTS = 3
        self.RECONNECT_INTERVAL = 5  # seconds

    async def connect(self, recorder: Recorder, server_url: str):
        """
        启动连接管理任务。
        :param recorder: 录音机实例
        :param server_url: VAD 服务器的 WebSocket URL
        """
        if self.is_running:
            logger.warning("连接任务已在运行中。")
            return
        
        self.recorder = recorder
        self.server_url = server_url
        self.is_running = True
        
        # 启动后台管理任务
        self._manage_task = asyncio.create_task(self._manage_connection())
        logger.info(f"已启动连接管理任务，目标服务器: {server_url}")

    async def _manage_connection(self):
        """
        后台任务：管理连接生命周期，处理连接建立和自动重连。
        """
        reconnect_attempts = 0

        while self.is_running:
            try:
                # 尝试建立连接并运行发送循环
                # 如果是重连，先等待一段时间
                if reconnect_attempts > 0:
                     logger.info(f"将在 {self.RECONNECT_INTERVAL} 秒后尝试第 {reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS} 次重连...")
                     await asyncio.sleep(self.RECONNECT_INTERVAL)

                logger.info("正在尝试连接 VAD 服务器...")
                await self._connect_and_run_sender()
                
                # 如果 _connect_and_run_sender 正常返回，说明是用户主动断开（is_running变为False）
                # 或者连接意外断开但没抛出异常（这取决于实现，目前的实现会抛出异常）
                # 这里我们假设正常返回意味着不需要重连
                reconnect_attempts = 0 # 重置计数器

            except Exception as e:
                logger.error(f"连接或发送过程中发生错误: {e}")
                # 检查是否应该重连
                if self.is_running:
                    reconnect_attempts += 1
                    if reconnect_attempts > self.MAX_RECONNECT_ATTEMPTS:
                        logger.error("达到最大重连次数，停止尝试。")
                        self.is_running = False
                        break
                else:
                    # 如果用户已经请求停止，就不再重连
                    break

    async def _connect_and_run_sender(self):
        """
        建立单次 WebSocket 连接并运行发送循环。
        如果连接断开或发生错误，会抛出异常以便上层捕获并触发重连。
        """
        try:
            async with websockets.connect(self.server_url) as websocket:
                logger.info(f"已连接到 VAD 服务器: {self.server_url}")
                
                # 连接成功，重置重连计数器的逻辑在上层
                
                # 启动录音
                try:
                    self.recorder.start()
                except Exception as e:
                    logger.error(f"录音机启动失败: {e}")
                    raise # 抛出异常，触发重连逻辑（或者如果是硬件错误，可能需要停止重连？）

                try:
                    target_samplerate = config.get("recorder", {}).get("target_samplerate", 16000)
                    
                    while self.is_running:
                        try:
                            # 设置超时，如果录音机队列长时间为空，不应该阻塞所有操作
                            # 这里使用 wait_for 并捕获 TimeoutError 也可以，
                            # 但为了简单，我们假设 recorder.q.get() 总是能在合理时间内返回
                            # 或者我们可以让其一直等待，直到 task 被 cancel
                            audio_data_int16 = await self.recorder.q.get()

                            # 检查是否需要重采样
                            if self.recorder.device_samplerate != target_samplerate:
                                audio_data_float32 = audio_data_int16.flatten().astype(np.float32) / 32768.0
                                resampled_data_float32 = resampy.resample(
                                    audio_data_float32,
                                    sr_orig=self.recorder.device_samplerate,
                                    sr_new=target_samplerate,
                                    filter='kaiser_fast'
                                )
                                final_audio_data = (resampled_data_float32 * 32768.0).astype(np.int16)
                            else:
                                final_audio_data = audio_data_int16
                            
                            await websocket.send(final_audio_data.tobytes())
                                
                        except asyncio.CancelledError:
                            raise # 允许任务被取消
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket 连接已关闭")
                            raise # 重新抛出，触发外层捕获
                        except Exception as e:
                            logger.error("音频发送循环发生错误", exc_info=True)
                            # 如果是 websockets 相关的其它错误，或者我们就认为是连接问题
                            # 我们可以尝试访问 protocol.state，但为了安全起见，
                            # 如果发送失败，我们假设连接可能不稳定，抛出异常触发重连往往是更安全的选择。
                            # 或者，我们只针对特定异常重连。
                            
                            # 这里做一个简单的检查：如果异常消息包含 connection closed 相关字眼
                            if "closed" in str(e).lower() or isinstance(e, (ConnectionError, BrokenPipeError)):
                                 raise ConnectionError("Connection issue detected") from e
                            
                            # 对于其他错误（如数据处理错误），我们可能希望继续尝试发送下一帧，
                            # 除非错误持续发生。但为了避免死循环报错，这里可以选择不抛出，继续循环。
                            
                finally:
                    # 确保退出循环时停止录音
                    self.recorder.stop()
                    
        except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError, ConnectionError) as e:
            logger.warning(f"WebSocket 连接中断: {e}")
            raise # 重新抛出，让 _manage_connection 处理重连

    async def disconnect(self):
        """用户主动请求断开连接。"""
        if not self.is_running:
            logger.warning("未连接到服务器或已停止。")
            return

        logger.info("正在断开连接...")
        self.is_running = False # 设置标志位，通知所有循环停止
        
        if self._manage_task:
            # 取消管理任务
            self._manage_task.cancel()
            try:
                await self._manage_task
            except asyncio.CancelledError:
                pass
            self._manage_task = None
        
        logger.info("已停止录音并断开连接。")

# 全局 WebSocket 管理器和录音机实例
websocket_manager = WebsocketManager()
recorder: Recorder = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 的生命周期事件，在应用启动时初始化录音机。"""
    global recorder
    load_config() # 在应用启动时加载配置

    # -- Numba JIT 编译器预热 --
    # resampy 内部使用 numba，首次调用会有一个显著的编译延迟，
    # 这会阻塞异步事件循环，导致音频 input overflow。
    # 我们在启动时执行一次虚拟的重采样操作，以提前触发编译。
    try:
        logger.info("正在预热音频重采样编译器 (numba)...")
        # resampy 需要一个足够长的信号来进行有意义的重采样，这里使用 1024 个样本
        _warmup_input = np.zeros(1024, dtype=np.float32)
        resampy.resample(_warmup_input, 48000, 16000)
        logger.info("编译器预热成功。")
    except Exception as e:
        logger.error(f"预热音频重采样编译器失败: {e}")
        # 这里不抛出异常，因为即使预热失败，程序仍可能工作，尽管首次处理会延迟。

    # Recorder 现在不需要任何参数，它会自动检测采样率
    recorder = Recorder()
    yield
    # 在应用关闭时，确保断开 WebSocket 连接
    if websocket_manager.is_running:
        await websocket_manager.disconnect()

app = FastAPI(lifespan=lifespan)

@app.post("/record/start")
async def start_record():
    """HTTP 端点，用于启动录音和 WebSocket 连接。"""
    if not recorder:
        raise HTTPException(status_code=500, detail="录音机未初始化")
    
    server_url = config.get("server_url")
    if not server_url:
        raise HTTPException(status_code=500, detail="配置文件中未找到 server_url")

    await websocket_manager.connect(recorder, server_url)
    return {"status": "录音已启动，正在连接"}

@app.post("/record/stop")
async def stop_record():
    """HTTP 端点，用于停止录音和断开 WebSocket 连接。"""
    await websocket_manager.disconnect()
    return {"status": "录音已停止，正在断开"}

if __name__ == "__main__":
    # 客户端运行在不同的端口以避免与服务器冲突
    uvicorn.run("app:app", host="0.0.0.0", port=8570, reload=True)
