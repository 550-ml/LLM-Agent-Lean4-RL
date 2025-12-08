"""
配置管理器：统一管理所有配置
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

import yaml

from src.logger import setup_logging


class ConfigManager:
    """配置管理器：统一加载和管理所有配置"""

    def __init__(self, config_file: str = "config/default.yaml"):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")

        with open(self.config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config or {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径，如 "llm.planning.model"）

        Args:
            key_path: 配置键路径（如 "llm.planning.model"）
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_data_config(self) -> Dict[str, Any]:
        """获取数据配置"""
        return self.config.get("data", {})

    def get_prompt_loader_config(self) -> Dict[str, Any]:
        """获取 prompt 加载器配置"""
        return self.config.get("prompt_loader", {})

    def get_retriever_config(self) -> Dict[str, Any]:
        """获取 retriever 配置"""
        return self.config.get("retriever", {})

    def get_llm_config(self, agent_type: str = "planning") -> Dict[str, Any]:
        """
        获取 LLM 配置

        Args:
            agent_type: 智能体类型（"planning" 或 "generation"）

        Returns:
            LLM 配置字典
        """
        return self.config.get("llm", {}).get(agent_type, {})

    def get_agent_config(self) -> Dict[str, Any]:
        """获取 Agent 配置"""
        return self.config.get("agent", {})

    def get_verifier_config(self) -> Dict[str, Any]:
        """获取验证器配置"""
        return self.config.get("verifier", {})

    def get_prover_config(self) -> Dict[str, Any]:
        """获取 Prover 配置"""
        return self.config.get("prover", {})

    def get_project_dir(self) -> str:
        """获取基准数据目录"""
        return self.get_data_config().get("project_dir", "data/benchmarks/lean4")

    def get_data_dir(self) -> str:
        """获取数据目录"""
        return self.get_data_config().get("data_dir", "data/benchmarks/lean4/test")

    def get_max_retries(self) -> int:
        """获取最大重试次数"""
        return self.get_agent_config().get("max_retries", 5)

    def init_logger(self):
        """
        根据时间创建一个文件夹，并返回文件夹路径
        """
        log_dir = self.get("logger.save_dir")
        log_config = self.get("logger.log_config")
        save_dir = datetime.now().strftime(f"{log_dir}/%Y%m%d_%H%M%S")
        os.makedirs(save_dir, exist_ok=True)
        setup_logging(sva_dir=save_dir, log_config=log_config)
        logger = logging.getLogger(__name__)
        return logger
