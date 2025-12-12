import logging
import queue
import sounddevice as sd

logger = logging.getLogger(__name__)


class Recorder:

    def __init__(self, samplerate=16000, channels=1, dtype="int16"):
        """Initializes the recorder."""
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.q = queue.Queue()
        self.stream = None
        self.is_recording = False
        logger.debug("Recorder instance created.")

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            logger.warning(f"Sounddevice status: {status}")
        self.q.put(indata.copy())

    def start(self):
        """Starts the audio recording."""
        if self.is_recording:
            logger.warning("Recorder is already running.")
            return

        logger.info("Starting audio stream...")
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._callback,
        )
        self.stream.start()
        self.is_recording = True
        logger.info("Audio stream started.")

    def stop(self):
        """Stops the audio recording."""
        if not self.is_recording:
            logger.warning("Recorder is not running.")
            return

        logger.info("Stopping audio stream...")
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_recording = False
        logger.info("Audio stream stopped.")
