import logging
from .base import STTEngine
from .dummy_engine import DummySTTEngine
from .funasr_engine import FunasrEngine

logger = logging.getLogger(__name__)

# STT 引擎注册表
# 当你添加新的 STT 引擎实现时，请在这里注册。
# 键是你在 config.yaml 中使用的引擎类型名称。
ENGINE_REGISTRY = {
    "dummy": DummySTTEngine,
    "funasr": FunasrEngine,
    # "whisper": WhisperEngine, # 示例：未来可以添加 Whisper 引擎
}

def get_stt_engine(config: dict) -> STTEngine:
    """
    STT 引擎工厂函数。

    根据提供的配置动态创建并返回一个 STT 引擎实例。

    :param config: STT 相关的配置字典。
                   预计包含一个 'type' 字段来指定要使用的引擎。
    :return: 一个 STTEngine 的实例。
    :raises ValueError: 如果配置中指定的引擎类型无效或未在注册表中找到。
    """
    engine_type = config.get("type", "dummy")
    logger.info(f"正在根据配置创建 STT 引擎，类型: '{engine_type}'")

    engine_class = ENGINE_REGISTRY.get(engine_type)

    if engine_class is None:
        raise ValueError(
            f"无效的 STT 引擎类型: '{engine_type}'。 "
            f"有效选项为: {list(ENGINE_REGISTRY.keys())}"
        )

    return engine_class(config)