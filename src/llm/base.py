"""
LLM 基础接口定义
参考 Lean4-LLM-Ai-Agent-Mooc 的 agents.py，但设计为更通用的抽象接口
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置类"""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）


@dataclass
class LLMResponse:
    """LLM 响应封装"""
    content: str
    model: str
    # tokens used (prompt_tokens, completion_tokens, total_tokens)
    usage: Dict[str, int]
    finish_reason: str = "stop"


class BaseLLM(ABC):
    """
    LLM 基础抽象类

    所有 LLM 实现都应该继承这个类，提供统一的接口
    参考 Lean4-LLM-Ai-Agent-Mooc 的 LLM_Agent 类，但更通用
    """

    def __init__(self, config: LLMConfig):
        """
        初始化 LLM

        Args:
            config: LLM 配置
        """
        self.config = config

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        生成响应

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数（如 temperature, max_tokens 等，会覆盖 config 中的设置）

        Returns:
            LLMResponse: LLM 响应对象
        """
        pass

    @abstractmethod
    def stream_generate(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式生成响应（可选实现）

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        pass

    def count_tokens(self, text: str) -> int:
        """
        计算 token 数量（可选实现，默认返回字符数）

        Args:
            text: 输入文本

        Returns:
            int: token 数量
        """
        # 默认实现：简单返回字符数（实际应该使用 tiktoken 等库）
        return len(text)

    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """
        验证消息格式

        Args:
            messages: 消息列表

        Returns:
            bool: 是否有效
        """
        if not messages:
            return False
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["system", "user", "assistant"]:
                return False
        return True

    def get_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        便捷方法：直接返回字符串响应
        这是为了兼容 Lean4-LLM-Ai-Agent-Mooc 的接口风格

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            str: LLM 生成的文本
        """
        response = self.generate(messages, **kwargs)
        return response.content
