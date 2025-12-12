from dataclasses import dataclass, field
from typing import List

@dataclass
class SleepRecordCreate:
    """用于创建新的睡眠记录的数据类"""
    timestamp: str
    duration: float
    audio_url: str
    transcription: str
    confidence: float = 0.0
    tags: List[str] = field(default_factory=list)
