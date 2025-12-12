from abc import ABC, abstractmethod

class STTEngine(ABC):
    """
    语音转文本 (STT) 引擎的抽象基类。
    所有具体的 STT 实现都应继承此类并实现 transcribe 方法。
    """

    @abstractmethod
    async def transcribe(self, wav_file_path: str) -> str:
        """
        将指定的 WAV 音频文件转换为文本。

        :param wav_file_path: 输入的 WAV 文件的路径。
        :return: 识别出的文本内容。
        """
        pass