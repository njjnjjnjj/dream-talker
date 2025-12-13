import logging
import asyncio
import sounddevice as sd

logger = logging.getLogger(__name__)


class Recorder:
    """
    录音机类，负责从麦克风捕获音频并将其放入异步队列中。
    """
    def __init__(self, samplerate=16000, channels=1, dtype="int16"):
        """初始化录音机。"""
        self.samplerate = samplerate  # 采样率
        self.channels = channels      # 声道数
        self.dtype = dtype            # 数据类型
        self.q = asyncio.Queue()      # 用于在回调和主异步循环之间传递音频数据的异步队列
        self.loop = asyncio.get_running_loop()
        self.stream = None            # sounddevice 的音频流对象
        self.is_recording = False     # 录音状态标志
        logger.debug("录音机实例已创建。")

    def _callback(self, indata, frames, time, status):
        """
        sounddevice 的回调函数，在每次捕获到音频块时被调用。
        这个函数在一个单独的线程中运行。
        """
        if status:
            logger.warning(f"Sounddevice 状态: {status}")
        
        try:
            # 使用从主线程获取的事件循环，确保线程安全
            self.loop.call_soon_threadsafe(self.q.put_nowait, indata.copy())
        except RuntimeError:
            # 如果事件循环已经关闭，这可能会发生。
            pass

    def start(self):
        """开始录音。"""
        if self.is_recording:
            logger.warning("录音机已在运行。")
            return

        logger.info("正在启动音频流...")
        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._callback,
            )
            self.stream.start()
            self.is_recording = True
            logger.info("音频流已启动。")
        except sd.PortAudioError as e:
            logger.error(f"启动音频流失败: {e}")
            self.is_recording = False
            # 尝试获取并记录可用的输入设备信息
            try:
                devices = sd.query_devices()
                input_devices = [d for d in devices if d['max_input_channels'] > 0]
                logger.error(f"可用的输入设备: {input_devices}")
            except Exception as device_error:
                logger.error(f"无法查询设备信息: {device_error}")
            raise # 重新抛出异常，让上层调用者处理
        except Exception as e:
            logger.error(f"启动音频流时发生未知错误: {e}")
            self.is_recording = False
            raise

    def stop(self):
        """停止录音。"""
        if not self.is_recording:
            logger.warning("录音机未在运行。")
            return

        logger.info("正在停止音频流...")
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_recording = False
        logger.info("音频流已停止。")
