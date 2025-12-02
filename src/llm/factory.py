"""
LLM 工厂类：根据配置创建对应的 LLM 实例
"""

from .base import BaseLLM, LLMConfig
from .openai_client import OpenAIClient
from .vllm_client import VLLMClient


class LLMFactory:
    """
    LLM 工厂类

    根据配置自动创建合适的 LLM 实例
    支持：
    - OpenAI API: gpt-*, o* 系列
    - vLLM 本地模型: vllm:model_name
    """

    @staticmethod
    def create_llm(config: LLMConfig) -> BaseLLM:
        """
        根据配置创建 LLM 实例

        Args:
            config: LLM 配置

        Returns:
            BaseLLM: LLM 实例

        Raises:
            ValueError: 如果模型名称不支持
        """
        model_name = config.model_name.lower()

        # OpenAI 模型（包括 GPT 系列和 O 系列）
        if model_name.startswith("gpt-") or (model_name.startswith("o") and not model_name.startswith("ollama")):
            return OpenAIClient(config)

        # vLLM 本地模型
        elif model_name.startswith("vllm:"):
            return VLLMClient(config)

        else:
            raise ValueError(f"Unsupported model: {config.model_name}. Supported models: gpt-*, o*, vllm:*")

    @staticmethod
    def create_from_dict(config_dict: dict) -> BaseLLM:
        """
        从字典创建 LLM 实例（便于从配置文件加载）

        Args:
            config_dict: 配置字典，包含 model_name, temperature 等

        Returns:
            BaseLLM: LLM 实例
        """
        config = LLMConfig(**config_dict)
        return LLMFactory.create_llm(config)
