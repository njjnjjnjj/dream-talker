import torch
import numpy as np
from typing import Callable, Coroutine
import logging
from silero_vad import VADIterator, load_silero_vad
import os
from datetime import datetime
import wave
from stt import STTEngine

logger = logging.getLogger(__name__)


class VadWrapper:
    """
    管理单个音频流的 VAD (Voice Activity Detection) 状态。
    它负责缓冲音频、检测语音，并在检测到完整的语音片段后通过回调函数将其返回。
    """

    def __init__(
        self,
        model,
        on_speech_end: Callable[[bytes], Coroutine],
        stt_engine: STTEngine,
        sample_rate: int = 16000,
        chunk_samples: int = 512,
        speech_pad_ms: int = 250,
        threshold: float = 0.5,
    ):
        # VAD 模型相关参数
        self.SAMPLE_RATE = sample_rate
        self.CHUNK_SAMPLES = chunk_samples
        self.CHUNK_BYTES = self.CHUNK_SAMPLES * 2  # 转换为字节大小 (16-bit PCM)

        self.SPEECH_PAD_MS = speech_pad_ms
        self.THRESHOLD = threshold

        # 用于存储音频数据
        self.DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "records")
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR)

        # 当检测到语音片段结束时调用的异步回调函数
        self._on_speech_end = on_speech_end
        self.stt_engine = stt_engine

        # 初始化 VAD 迭代器
        self.vad_iterator = VADIterator(
            model,
            threshold=self.THRESHOLD,
            speech_pad_ms=self.SPEECH_PAD_MS
        )

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

    def _save_audio(self, audio_bytes: bytes) -> str | None:
        """
        将音频数据保存为 WAV 文件。
        :return: 成功则返回文件路径，失败则返回 None。
        """
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".wav"
        filepath = os.path.join(self.DATA_DIR, filename)

        try:
            with wave.open(filepath, "wb") as wf:
                wf.setnchannels(1)  # 单声道
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(audio_bytes)
            logger.info(f"语音片段已保存至: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
            return None

    async def process(self, audio_bytes: bytes):
        """
        处理从客户端流式传输过来的音频数据块。
        :param audio_bytes: 从 WebSocket 接收到的原始音频字节
        """
        self._incoming_buffer.extend(audio_bytes)

        while len(self._incoming_buffer) >= self.CHUNK_BYTES:
            chunk = self._incoming_buffer[: self.CHUNK_BYTES]
            del self._incoming_buffer[: self.CHUNK_BYTES]

            self._history_buffer.extend(chunk)
            if len(self._history_buffer) > self._history_buffer_max_size:
                start = len(self._history_buffer) - self._history_buffer_max_size
                self._history_buffer = self._history_buffer[start:]

            audio_tensor = (
                torch.from_numpy(np.frombuffer(chunk, dtype=np.int16)).float() / 32768.0
            )
            speech_dict = self.vad_iterator(audio_tensor)

            if speech_dict:
                if "start" in speech_dict:
                    if not self._is_speaking:
                        logger.debug("检测到语音开始")
                        self._is_speaking = True
                        self._speech_buffer.extend(self._history_buffer)
                        self._history_buffer.clear()

                if "end" in speech_dict:
                    if self._is_speaking:
                        self._is_speaking = False
                        self._speech_buffer.extend(chunk)
                        logger.debug(
                            f"检测到语音结束，片段大小: {len(self._speech_buffer)} 字节。"
                        )
                        speech_data = bytes(self._speech_buffer)
                        wav_path = self._save_audio(speech_data)

                        if wav_path and self.stt_engine:
                            transcript = await self.stt_engine.transcribe(wav_path)
                            logger.info(f"STT 识别结果: {transcript}")

                        await self._on_speech_end(speech_data)
                        self._speech_buffer.clear()
                        self.vad_iterator.reset_states()

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

    def __init__(self, vad_config: dict = None):
        logger.info("正在加载 Silero VAD 模型...")
        self.model = load_silero_vad()
        self.vad_config = vad_config if vad_config is not None else {}
        logger.info("Silero VAD 模型加载成功。")

    def get_vad_wrapper(
        self, on_speech_end: Callable[[bytes], Coroutine], stt_engine: STTEngine
    ):
        """
        为每个客户端连接创建一个新的 VadWrapper 实例。
        :param on_speech_end: 语音片段结束时的回调函数
        :param stt_engine: STT 引擎实例
        """
        return VadWrapper(
            self.model,
            on_speech_end,
            stt_engine=stt_engine,
            **self.vad_config,
        )
