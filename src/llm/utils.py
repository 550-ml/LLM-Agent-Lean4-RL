"""
LLM 工具函数
"""

import logging
from typing import List, Dict, Optional
from .base import LLMConfig, BaseLLM

logger = logging.getLogger(__name__)


def estimate_cost(tokens: int, model_name: str) -> float:
    """
    估算 API 调用成本（美元）

    Args:
        tokens: token 数量
        model_name: 模型名称

    Returns:
        float: 估算成本（美元）
    """
    # OpenAI 定价（2024年，可能已过时，仅供参考）
    pricing = {
        "gpt-4o": {"input": 2.5 / 1_000_000, "output": 10.0 / 1_000_000},
        "gpt-4": {"input": 30.0 / 1_000_000, "output": 60.0 / 1_000_000},
        "gpt-4-turbo": {"input": 10.0 / 1_000_000, "output": 30.0 / 1_000_000},
        "gpt-3.5-turbo": {"input": 0.5 / 1_000_000, "output": 1.5 / 1_000_000},
        "o1-preview": {"input": 15.0 / 1_000_000, "output": 60.0 / 1_000_000},
        "o1-mini": {"input": 3.0 / 1_000_000, "output": 12.0 / 1_000_000},
        "o3-mini": {"input": 3.0 / 1_000_000, "output": 12.0 / 1_000_000},
    }

    # 默认使用 gpt-4o 的定价
    model_pricing = pricing.get(model_name, pricing["gpt-4o"])

    # 假设输入和输出各占一半（粗略估算）
    input_cost = (tokens // 2) * model_pricing["input"]
    output_cost = (tokens // 2) * model_pricing["output"]

    return input_cost + output_cost


def format_messages_for_logging(messages: List[Dict[str, str]], max_length: int = 200) -> str:
    """
    格式化消息用于日志记录

    Args:
        messages: 消息列表
        max_length: 每条消息的最大显示长度

    Returns:
        str: 格式化后的消息字符串
    """
    formatted = []
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if len(content) > max_length:
            content = content[:max_length] + "..."
        formatted.append(f"[{i+1}] {role}: {content}")
    return "\n".join(formatted)


def validate_config(config: LLMConfig) -> bool:
    """
    验证配置是否有效

    Args:
        config: LLM 配置

    Returns:
        bool: 是否有效
    """
    if not config.model_name:
        logger.error("Model name is required")
        return False

    if config.temperature < 0 or config.temperature > 2:
        logger.warning(
            f"Temperature {config.temperature} is outside recommended range [0, 2]")

    if config.max_tokens < 1:
        logger.error("max_tokens must be positive")
        return False

    if config.top_p < 0 or config.top_p > 1:
        logger.error("top_p must be in range [0, 1]")
        return False

    return True
