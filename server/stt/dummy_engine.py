import asyncio
import logging
from .base import STTEngine

logger = logging.getLogger(__name__)

class DummySTTEngine(STTEngine):
    """
    一个虚拟的 STT 引擎，用于测试和开发。
    它不执行任何实际的语音识别，而是返回一个固定的字符串。
    """

    def __init__(self, config: dict = None):
        """
        初始化虚拟 STT 引擎。
        :param config: (可选) 配置字典，此处未使用。
        """
        logger.info("初始化 DummySTTEngine。")

    async def transcribe(self, wav_file_path: str) -> str:
        """
        模拟语音转文本的过程。

        :param wav_file_path: 输入的 WAV 文件的路径（此处未使用）。
        :return: 一个固定的文本字符串。
        """
        logger.info(f"DummySTTEngine 正在 '处理' 文件: {wav_file_path}")
        # 模拟一个网络或模型处理的延迟
        await asyncio.sleep(0.1)
        result = "这是一个来自虚拟 STT 引擎的测试结果。"
        logger.info(f"DummySTTEngine 返回结果: {result}")
        return result