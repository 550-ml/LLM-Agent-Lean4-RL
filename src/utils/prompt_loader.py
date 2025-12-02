"""
Prompt 加载工具

从外部文件加载 prompt 模板，支持变量替换
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# class PromptLoader:
#     def __init__(self, prompts_dir: str = 'data/prompts'):
#         # 1. absolute
#         prompts_path = Path(prompts_dir)
#         if not prompts_path.is_absolute():
#             current_file = Path(__file__)
#             project_root = current_file.parent.parent.parent
#             prompts_path = project_root / prompts_dir

#             if not prompts_path.exists():
#                 prompts_path = Path(prompts_dir)

#         self.prompts_dir = prompts_path
#         self._cache = {}

#         # 2. not
#         if not self.prompts_dir.exists():
#             logger.warning(
#                 f"Prompt 目录不存在: {self.prompts_dir}. "
#                 f"请确保目录存在或使用正确的路径。"
#             )
#         else:
#             logger.info(f"Prompt 加载器初始化，目录: {self.prompts_dir}")

#     def load_system_prompt(self, name: str) -> str:
#         """
#         加载 system prompt
#         """
#         return self._load_prompt("system", name)


class PromptLoader:
    """Prompt 模板加载器"""

    def __init__(self, prompts_dir: str = "data/prompts"):
        """
        初始化 Prompt 加载器

        Args:
            prompts_dir: prompt 文件目录（可以是绝对路径或相对路径）
        """
        # 处理路径：如果是相对路径，尝试从项目根目录查找
        prompts_path = Path(prompts_dir)
        if not prompts_path.is_absolute():
            # 尝试从当前文件所在位置向上查找项目根目录
            current_file = Path(__file__)
            # src/utils -> src -> project_root
            project_root = current_file.parent.parent.parent
            prompts_path = project_root / prompts_dir

            # 如果不存在，尝试直接使用相对路径
            if not prompts_path.exists():
                prompts_path = Path(prompts_dir)

        self.prompts_dir = prompts_path
        self._cache: Dict[str, str] = {}

        # 验证目录存在
        if not self.prompts_dir.exists():
            logger.warning(
                f"Prompt 目录不存在: {self.prompts_dir}. "
                f"请确保目录存在或使用正确的路径。"
            )
        else:
            logger.info(f"Prompt 加载器初始化，目录: {self.prompts_dir}")

    def load_system_prompt(self, name: str) -> str:
        """
        加载 system prompt

        Args:
            name: prompt 文件名（不含扩展名）

        Returns:
            prompt 内容

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        return self._load_prompt("system", name)

    def load_user_prompt(self, name: str) -> str:
        """
        加载 user prompt

        Args:
            name: prompt 文件名（不含扩展名）

        Returns:
            prompt 内容

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        return self._load_prompt("user", name)

    def _load_prompt(self, category: str, name: str) -> str:
        """
        加载 prompt 文件

        Args:
            category: 类别（system 或 user）
            name: 文件名（不含扩展名）

        Returns:
            prompt 内容

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        cache_key = f"{category}/{name}"

        # 检查缓存
        if cache_key in self._cache:
            logger.debug(f"从缓存加载 prompt: {cache_key}")
            return self._cache[cache_key]

        # 构建文件路径（支持 .md 和 .txt）
        for ext in [".md", ".txt"]:
            file_path = self.prompts_dir / category / f"{name}{ext}"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        self._cache[cache_key] = content
                        logger.debug(f"加载 prompt: {file_path}")
                        return content
                except Exception as e:
                    logger.error(f"读取 prompt 文件失败 {file_path}: {e}")
                    raise

        # 文件不存在
        error_msg = (
            f"Prompt 文件未找到: {self.prompts_dir / category / name} "
            f"(已尝试 .md 和 .txt 扩展名)"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    def format_prompt(self, template: str, **kwargs) -> str:
        """
        格式化 prompt 模板（支持 {variable} 替换）

        Args:
            template: prompt 模板
            **kwargs: 要替换的变量

        Returns:
            格式化后的 prompt

        Raises:
            ValueError: 如果缺少必需的变量
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            error_msg = f"Prompt 模板缺少变量: {missing_var}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def load_and_format(
        self,
        category: str,
        name: str,
        **kwargs
    ) -> str:
        """
        加载并格式化 prompt（便捷方法）

        Args:
            category: 类别（system 或 user）
            name: 文件名（不含扩展名）
            **kwargs: 要替换的变量

        Returns:
            格式化后的 prompt

        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果缺少必需的变量
        """
        template = self._load_prompt(category, name)
        if kwargs:
            return self.format_prompt(template, **kwargs)
        return template

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.debug("Prompt 缓存已清空")

    def list_available_prompts(self, category: Optional[str] = None) -> Dict[str, list]:
        """
        列出可用的 prompt 文件

        Args:
            category: 类别（system 或 user），如果为 None 则列出所有

        Returns:
            字典，键为类别，值为文件名列表
        """
        result = {}
        categories = [category] if category else ["system", "user"]

        for cat in categories:
            cat_dir = self.prompts_dir / cat
            if cat_dir.exists():
                files = []
                for ext in [".md", ".txt"]:
                    for file_path in cat_dir.glob(f"*{ext}"):
                        # 移除扩展名
                        name = file_path.stem
                        if name not in files:
                            files.append(name)
                result[cat] = sorted(files)
            else:
                result[cat] = []

        return result


# 全局实例（可选，用于单例模式）
_default_loader: Optional[PromptLoader] = None


def get_prompt_loader(prompts_dir: str = "data/prompts") -> PromptLoader:
    """
    获取全局 PromptLoader 实例（单例模式）

    Args:
        prompts_dir: prompt 文件目录

    Returns:
        PromptLoader 实例
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader(prompts_dir)
    return _default_loader


def reset_prompt_loader():
    """重置全局 PromptLoader 实例（用于测试）"""
    global _default_loader
    _default_loader = None
