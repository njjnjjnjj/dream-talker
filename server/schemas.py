from dataclasses import dataclass, field
from typing import List, Dict, Union

@dataclass
class SleepRecordCreate:
    """用于创建新的睡眠记录的数据类"""
    timestamp: str
    duration: float
    audio_url: str
    transcription: str
    confidence: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class SleepRecord:
    """用于从数据库返回睡眠记录的数据类，包含 id"""
    id: int
    timestamp: str
    duration: float
    audio_url: str
    transcription: str
    confidence: float = 0.0
    is_favorite: bool = False # 添加 is_favorite 字段
    tags: List[str] = field(default_factory=list)


@dataclass
class DailyActivitySummary:
    """用于表示每天的记录活动总结"""
    total_records: int = 0
    favorite_records: int = 0


@dataclass
class MonthlyActivity:
    """用于从数据库返回每月活动记录数量的数据类"""
    activity: Dict[str, DailyActivitySummary] = field(default_factory=dict)
