import logging
import asyncio
import sounddevice as sd
import platform # 导入 platform 模块

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
        # self.device = device          # 音频设备，现在将自动发现
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
        """
        开始录音。
        实现智能设备选择逻辑：
        1. 尝试使用默认设备。
        2. 如果默认设备因采样率问题失败，则在 Linux 系统上尝试查找并使用 'plughw' 设备。
        """
        if self.is_recording:
            logger.warning("录音机已在运行。")
            return

        logger.info("正在启动音频流...")
        
        # 尝试使用的设备列表
        devices_to_try = [None] # None 表示使用 sounddevice 的默认设备

        # 如果是 Linux 系统，并且设备是 USB 音频设备，则尝试查找 plughw 设备
        if platform.system() == "Linux":
            try:
                available_devices = sd.query_devices()
                # 寻找名称中包含 'plughw' 的输入设备
                plughw_devices = [
                    d['name'] for d in available_devices
                    if 'plughw' in d['name'] and d['max_input_channels'] > 0
                ]
                if plughw_devices:
                    # 将找到的 plughw 设备添加到尝试列表中，优先使用默认设备
                    devices_to_try.extend(plughw_devices)
                    logger.debug(f"在 Linux 上找到 {len(plughw_devices)} 个 plughw 设备: {plughw_devices}")
                else:
                    logger.debug("在 Linux 上未找到任何 'plughw' 设备。")
            except Exception as e:
                logger.warning(f"查询设备失败，无法自动发现 plughw 设备: {e}")

        # 遍历尝试所有设备
        last_error = None
        for device_name in devices_to_try:
            try:
                logger.info(f"正在尝试使用设备: {device_name if device_name else '默认设备'}...")
                self.stream = sd.InputStream(
                    samplerate=self.samplerate,
                    channels=self.channels,
                    dtype=self.dtype,
                    callback=self._callback,
                    device=device_name, # 传递当前尝试的设备名
                )
                self.stream.start()
                self.is_recording = True
                logger.info(f"音频流已通过设备 '{device_name if device_name else '默认设备'}' 成功启动。")
                return # 成功启动，退出函数
            except sd.PortAudioError as e:
                last_error = e
                if 'Invalid sample rate' in str(e):
                    logger.warning(f"设备 '{device_name if device_name else '默认设备'}' 不支持所需采样率。")
                else:
                    logger.error(f"启动音频流失败，设备 '{device_name if device_name else '默认设备'}' 发生 PortAudioError: {e}")
            except Exception as e:
                last_error = e
                logger.error(f"启动音频流时发生未知错误，设备 '{device_name if device_name else '默认设备'}'：{e}")
        
        # 如果所有尝试都失败了，则抛出最后一个错误
        self.is_recording = False
        if last_error:
            logger.error(f"所有尝试的设备都未能启动音频流。最终错误: {last_error}")
            raise last_error
        else:
            # 这应该不会发生，但以防万一
            final_error = Exception("无法启动音频流，没有可用的设备或所有设备尝试均失败。")
            logger.error(final_error)
            raise final_error

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
