"""
OpenAI API 客户端实现
参考 Lean4-LLM-Ai-Agent-Mooc 的 agents.py
"""

import os
import time
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError

from .base import BaseLLM, LLMConfig, LLMResponse, logger


class OpenAIClient(BaseLLM):
    """
    OpenAI API 客户端

    支持所有 OpenAI 兼容的模型：
    - gpt-4o, gpt-4, gpt-3.5-turbo
    - o3-mini, o1-preview 等
    """

    def __init__(self, config: LLMConfig):
        """
        初始化 OpenAI 客户端

        Args:
            config: LLM 配置
        """
        super().__init__(config)

        # 从环境变量或配置中获取 API key
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it in config.")

        # 创建 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.base_url,  # 支持自定义 base_url（如用于代理）
            timeout=config.timeout
        )

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        生成响应（带重试机制）

        Args:
            messages: 消息列表
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            LLMResponse: LLM 响应对象

        Raises:
            ValueError: 如果消息格式无效
            APIError: 如果 API 调用失败
        """
        # 验证消息格式
        if not self.validate_messages(messages):
            raise ValueError(
                "Invalid messages format. Messages must be a list of dicts with 'role' and 'content' keys.")

        # 合并配置和 kwargs
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        top_p = kwargs.get("top_p", self.config.top_p)
        frequency_penalty = kwargs.get(
            "frequency_penalty", self.config.frequency_penalty)
        presence_penalty = kwargs.get(
            "presence_penalty", self.config.presence_penalty)

        # 准备 API 参数
        api_params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        # 某些模型不支持这些参数（如 o1 系列）
        if self.config.model_name not in ["o1-preview", "o1-mini"]:
            api_params["frequency_penalty"] = frequency_penalty
            api_params["presence_penalty"] = presence_penalty

        # 重试机制
        max_retries = kwargs.get("max_retries", self.config.max_retries)
        retry_delay = kwargs.get("retry_delay", self.config.retry_delay)

        last_error = None
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"OpenAI API call (attempt {attempt + 1}/{max_retries}): model={self.config.model_name}")

                # 调用 OpenAI API
                completion = self.client.chat.completions.create(**api_params)

                # 提取响应
                choice = completion.choices[0]
                content = choice.message.content or ""

                # 构建响应对象
                usage = {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0,
                }

                logger.debug(
                    f"OpenAI API success: tokens={usage['total_tokens']}, finish_reason={choice.finish_reason}")

                return LLMResponse(
                    content=content,
                    model=completion.model,
                    usage=usage,
                    finish_reason=choice.finish_reason or "stop"
                )

            except RateLimitError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"Rate limit exceeded, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Rate limit exceeded after {max_retries} attempts")
                    raise

            except APIConnectionError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"API connection error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"API connection failed after {max_retries} attempts")
                    raise

            except APIError as e:
                # 其他 API 错误，不重试
                logger.error(f"OpenAI API error: {e}")
                raise

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Unexpected error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    raise

        # 如果所有重试都失败
        raise last_error if last_error else Exception("Unknown error occurred")

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """
        流式生成响应

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        # 验证消息格式
        if not self.validate_messages(messages):
            raise ValueError("Invalid messages format")

        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        top_p = kwargs.get("top_p", self.config.top_p)
        frequency_penalty = kwargs.get(
            "frequency_penalty", self.config.frequency_penalty)
        presence_penalty = kwargs.get(
            "presence_penalty", self.config.presence_penalty)

        api_params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True
        }

        # o1 系列不支持这些参数
        if self.config.model_name not in ["o1-preview", "o1-mini"]:
            api_params["frequency_penalty"] = frequency_penalty
            api_params["presence_penalty"] = presence_penalty

        try:
            stream = self.client.chat.completions.create(**api_params)

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        使用 tiktoken 计算 token 数量（如果可用）

        Args:
            text: 输入文本

        Returns:
            int: token 数量
        """
        try:
            import tiktoken
            # 对于 o1 系列，使用 cl100k_base 编码
            if self.config.model_name in ["o1-preview", "o1-mini"]:
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                try:
                    encoding = tiktoken.encoding_for_model(
                        self.config.model_name)
                except KeyError:
                    # 如果模型不在 tiktoken 的已知列表中，使用默认编码
                    encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))
        except ImportError:
            logger.warning(
                "tiktoken not available, using character count as approximation")
            # 粗略估算：1 token ≈ 4 个字符（英文）
            return len(text) // 4
        except Exception as e:
            logger.warning(
                f"Error counting tokens: {e}, using character count")
            return len(text) // 4
