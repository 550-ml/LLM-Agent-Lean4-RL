"""
vLLM 客户端实现
vLLM 提供 OpenAI 兼容的 API，所以可以复用 OpenAI 客户端的逻辑
"""

import os
import logging
from typing import List, Dict
from openai import OpenAI

from .base import BaseLLM, LLMConfig, LLMResponse
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class VLLMClient(OpenAIClient):
    """
    vLLM 客户端

    vLLM 提供 OpenAI 兼容的 API，所以继承 OpenAIClient
    主要区别是：
    1. 使用本地 vLLM 服务器的 base_url
    2. 模型名称需要去掉 "vllm:" 前缀
    3. API key 可以是任意值（vLLM 通常不需要验证）
    """

    def __init__(self, config: LLMConfig):
        """
        初始化 vLLM 客户端

        Args:
            config: LLM 配置，model_name 格式应为 "vllm:model_name"
        """
        # 提取实际的模型名称（去掉 vllm: 前缀）
        if config.model_name.startswith("vllm:"):
            actual_model_name = config.model_name.replace("vllm:", "", 1)
        else:
            actual_model_name = config.model_name
            logger.warning(
                f"vLLM model name should start with 'vllm:', got {config.model_name}")

        # 从环境变量获取 base_url，默认为本地 vLLM 服务器地址
        base_url = config.base_url or os.getenv(
            "VLLM_BASE_URL", "http://127.0.0.1:8000/v1")

        # vLLM 通常不需要 API key，但为了兼容 OpenAI API，可以使用任意值
        api_key = config.api_key or os.getenv("VLLM_API_KEY", "EMPTY")

        # 创建新的配置，使用实际的模型名称和 vLLM 的 base_url
        vllm_config = LLMConfig(
            model_name=actual_model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            api_key=api_key,
            base_url=base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )

        # 调用父类初始化
        # 注意：OpenAIClient 会检查 API key，但我们已经设置了 api_key="EMPTY"
        # 对于 vLLM，API key 可以是任意值
        super().__init__(vllm_config)

        # 保存原始配置中的模型名称（带 vllm: 前缀）
        self.original_model_name = config.model_name

        logger.info(
            f"Initialized vLLM client: model={actual_model_name}, base_url={base_url}")
