"""
LLM 配置加载器
从 YAML 文件或字典加载配置
"""

import os
import yaml
from typing import Dict, Optional
from .base import LLMConfig


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_config_section(file_path: str, section: str) -> Dict:
        """
        加载配置文件的某个节

        Args:
            file_path: YAML 文件路径
            section: 配置节路径（如 "llm.planning" 或 "data"）

        Returns:
            Dict: 配置字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 解析节路径
        keys = section.split('.')
        for key in keys:
            if key in data:
                data = data[key]
            else:
                raise KeyError(f"配置节 '{section}' 不存在于 {file_path}")

        return data

    @staticmethod
    def load_from_yaml(file_path: str, section: Optional[str] = None) -> LLMConfig:
        """
        从 YAML 文件加载配置

        Args:
            file_path: YAML 文件路径
            section: 配置节名称（如 "llm.planning" 或 "llm.generation"）

        Returns:
            LLMConfig: LLM 配置对象

        Example:
            # 从 default.yaml 加载规划模型配置
            config = ConfigLoader.load_from_yaml("config/default.yaml", "llm.planning")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 如果指定了 section，提取对应的配置
        if section:
            keys = section.split('.')
            for key in keys:
                if key in data:
                    data = data[key]
                else:
                    raise KeyError(f"配置节 '{section}' 不存在于 {file_path}")

        return ConfigLoader.load_from_dict(data)

    @staticmethod
    def load_from_dict(config_dict: Dict) -> LLMConfig:
        """
        从字典加载配置

        Args:
            config_dict: 配置字典

        Returns:
            LLMConfig: LLM 配置对象

        Example:
            config = ConfigLoader.load_from_dict({
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 2048
            })
        """
        # 处理 model 键（可能是 "model" 或 "model_name"）
        model_name = config_dict.get("model") or config_dict.get("model_name")
        if not model_name:
            raise ValueError("配置中必须包含 'model' 或 'model_name' 字段")

        # 从环境变量获取 API key（如果配置中没有）
        api_key = config_dict.get("api_key") or os.getenv("OPENAI_API_KEY")

        # 构建配置对象
        return LLMConfig(
            model_name=model_name,
            temperature=config_dict.get("temperature", 0.7),
            max_tokens=config_dict.get("max_tokens", 2048),
            top_p=config_dict.get("top_p", 1.0),
            frequency_penalty=config_dict.get("frequency_penalty", 0.0),
            presence_penalty=config_dict.get("presence_penalty", 0.0),
            api_key=api_key,
            base_url=config_dict.get("base_url"),
            timeout=config_dict.get("timeout", 60),
            max_retries=config_dict.get("max_retries", 3),
            retry_delay=config_dict.get("retry_delay", 1.0)
        )

    @staticmethod
    def load_planning_config(file_path: str = "config/default.yaml") -> LLMConfig:
        """
        加载规划智能体的配置（便捷方法）

        Args:
            file_path: 配置文件路径

        Returns:
            LLMConfig: 规划智能体的配置
        """
        return ConfigLoader.load_from_yaml(file_path, "llm.planning")

    @staticmethod
    def load_generation_config(file_path: str = "config/default.yaml") -> LLMConfig:
        """
        加载生成智能体的配置（便捷方法）

        Args:
            file_path: 配置文件路径

        Returns:
            LLMConfig: 生成智能体的配置
        """
        return ConfigLoader.load_from_yaml(file_path, "llm.generation")
