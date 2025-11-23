"""
LLM 工厂类：根据配置创建对应的 LLM 实例
"""

from typing import Optional
from .base import BaseLLM, LLMConfig
from .openai_client import OpenAIClient


class LLMFactory:
    """
    LLM 工厂类
    
    根据配置自动创建合适的 LLM 实例
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
        if model_name.startswith("gpt-") or model_name.startswith("o"):
            return OpenAIClient(config)
        
        # vLLM 本地模型（未来实现）
        elif model_name.startswith("vllm:"):
            raise NotImplementedError("vLLM client not yet implemented")
            # from .vllm_client import VLLMClient
            # return VLLMClient(config)
        
        # Ollama 本地模型（未来实现）
        elif model_name.startswith("ollama:"):
            raise NotImplementedError("Ollama client not yet implemented")
            # from .ollama_client import OllamaClient
            # return OllamaClient(config)
        
        else:
            raise ValueError(f"Unsupported model: {config.model_name}. "
                           f"Supported models: gpt-*, o*, vllm:*, ollama:*")
    
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

