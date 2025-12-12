import logging
from .base import STTEngine
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess


logger = logging.getLogger(__name__)


class FunasrEngine(STTEngine):
    """
    使用阿里 FunASR 进行语音转文本的引擎。
    这是一个本地 STT 实现
    """

    def __init__(
        self,
        model_name="",
    ):
        model_dir = "iic/SenseVoiceSmall"
        self.model = AutoModel(
            model=model_dir,
            vad_model="fsmn-vad",
            vad_kwargs={"max_single_segment_time": 30000},
            device="cpu",
        )

    async def transcribe(self, wav_file_path: str) -> str:
        res = self.model.generate(
            input=wav_file_path,
            cache={},
            language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
            use_itn=True,
            batch_size_s=60,
            merge_vad=True,  #
            merge_length_s=15,
        )
        text = rich_transcription_postprocess(res[0]["text"])
        return text
