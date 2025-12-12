import torch
import numpy as np
from typing import Callable, Coroutine
import logging
from silero_vad import VADIterator, load_silero_vad

logger = logging.getLogger(__name__)

class VadWrapper:
    """
    管理单个音频流的 VAD (Voice Activity Detection) 状态。
    它负责缓冲音频、检测语音，并在检测到完整的语音片段后通过回调函数将其返回。
    """
    def __init__(self, model, on_speech_end: Callable[[bytes], Coroutine]):
        # VAD 模型相关参数
        self.SAMPLE_RATE = 16000  # VAD 模型期望的采样率
        self.CHUNK_SAMPLES = 512  # 每次处理的音频块大小 (32ms @ 16kHz)，这是 Silero VAD 支持的块大小
        self.CHUNK_BYTES = self.CHUNK_SAMPLES * 2  # 转换为字节大小 (16-bit PCM)
        
        self.SPEECH_PAD_MS = 250  # 在语音片段前后添加的静音填充，以防语音被意外切断
        self.THRESHOLD = 0.5  # VAD 检测的置信度阈值
        
        # 当检测到语音片段结束时调用的异步回调函数
        self._on_speech_end = on_speech_end
        
        # 初始化 VAD 迭代器
        self.vad_iterator = VADIterator(model,
                                        threshold=self.THRESHOLD,
                                        speech_pad_ms=self.SPEECH_PAD_MS,
                                        ) # 最短语音时长
        
        # 用于暂存从客户端接收到的音频数据
        self._incoming_buffer = bytearray()
        
        # 计算历史缓冲区的最大字节数，用于在语音开始时，将填充部分包含进来
        padding_bytes = self.SPEECH_PAD_MS * (self.SAMPLE_RATE // 1000) * 2
        # 历史音频数据缓冲区
        self._history_buffer = bytearray()
        self._history_buffer_max_size = padding_bytes
        
        # 用于存储当前正在检测的语音数据
        self._speech_buffer = bytearray()
        # 标记当前是否处于说话状态
        self._is_speaking = False

    async def process(self, audio_bytes: bytes):
        """
        处理从客户端流式传输过来的音频数据块。
        :param audio_bytes: 从 WebSocket 接收到的原始音频字节
        """
        # 将新接收到的音频数据追加到输入缓冲区
        self._incoming_buffer.extend(audio_bytes)
        
        # 只要缓冲区中的数据足够一个处理块，就循环处理
        while len(self._incoming_buffer) >= self.CHUNK_BYTES:
            # 从缓冲区取出一个音频块
            chunk = self._incoming_buffer[:self.CHUNK_BYTES]
            del self._incoming_buffer[:self.CHUNK_BYTES]
            
            # 将当前块添加到历史缓冲区，并确保其不超过最大长度
            self._history_buffer.extend(chunk)
            if len(self._history_buffer) > self._history_buffer_max_size:
                start = len(self._history_buffer) - self._history_buffer_max_size
                self._history_buffer = self._history_buffer[start:]

            # 将 16-bit PCM 音频数据转换为 VAD 模型期望的 float tensor
            audio_tensor = torch.from_numpy(np.frombuffer(chunk, dtype=np.int16)).float() / 32768.0
            # 使用 VAD 迭代器进行语音活动检测
            speech_dict = self.vad_iterator(audio_tensor)
            
            if speech_dict:
                # 检测到语音开始
                if "start" in speech_dict:
                    if not self._is_speaking:
                        logger.debug("检测到语音开始")
                        self._is_speaking = True
                        # 将历史缓冲区的数据（即填充部分）添加到语音缓冲区
                        self._speech_buffer.extend(self._history_buffer)
                        self._history_buffer.clear()
                
                # 检测到语音结束
                if "end" in speech_dict:
                    if self._is_speaking:
                        self._is_speaking = False
                        # 将当前块也添加到语音缓冲区
                        self._speech_buffer.extend(chunk)
                        logger.debug(f"检测到语音结束，片段大小: {len(self._speech_buffer)} 字节。")
                        # 触发语音结束回调
                        await self._on_speech_end(bytes(self._speech_buffer))
                        # 清空语音缓冲区，为下一段语音做准备
                        self._speech_buffer.clear()
                        # 重置 VAD 状态
                        self.vad_iterator.reset_states()
            
            # 如果当前正在说话，持续将音频块添加到语音缓冲区
            if self._is_speaking:
                self._speech_buffer.extend(chunk)

    def reset(self):
        """为新的音频流重置 VAD 状态，清空所有缓冲区。"""
        self.vad_iterator.reset_states()
        self._incoming_buffer.clear()
        self._history_buffer.clear()
        self._speech_buffer.clear()
        self._is_speaking = False

class VadEngine:
    """
    这个类负责在服务启动时预加载 VAD 模型，
    并为每个新的客户端连接提供一个配置好的 VadWrapper 实例。
    """
    def __init__(self):
        logger.info("正在加载 Silero VAD 模型...")
        # 根据用户要求，使用 pip 安装的包来加载模型，而不是 torch.hub
        self.model = load_silero_vad()
        logger.info("Silero VAD 模型加载成功。")

    def get_vad_wrapper(self, on_speech_end: Callable[[bytes], Coroutine]):
        """
        为每个客户端连接创建一个新的 VadWrapper 实例。
        :param on_speech_end: 语音片段结束时的回调函数
        """
        return VadWrapper(self.model, on_speech_end)
