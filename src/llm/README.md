# LLM 模块改进说明

## ✅ 已完成的改进

### 1. **增强的配置类 (LLMConfig)**

新增配置项：
- `frequency_penalty`: 频率惩罚（0.0-2.0）
- `presence_penalty`: 存在惩罚（0.0-2.0）
- `max_retries`: 最大重试次数（默认 3）
- `retry_delay`: 重试延迟（默认 1.0 秒）

### 2. **错误处理和重试机制**

- ✅ **自动重试**: 遇到 RateLimitError 或 APIConnectionError 时自动重试
- ✅ **指数退避**: 重试延迟按指数增长（1s, 2s, 4s...）
- ✅ **错误分类**: 区分不同类型的错误（速率限制、连接错误、API 错误）
- ✅ **详细日志**: 记录每次重试和错误信息

### 3. **消息验证**

- ✅ **格式检查**: 验证消息格式是否正确
- ✅ **角色验证**: 确保角色是 system/user/assistant 之一
- ✅ **内容检查**: 确保每条消息都有 content 字段

### 4. **Token 计数改进**

- ✅ **tiktoken 支持**: 使用 tiktoken 精确计算 token
- ✅ **o1 系列支持**: 正确处理 o1-preview 和 o1-mini 的编码
- ✅ **降级处理**: 如果 tiktoken 不可用，使用字符数估算

### 5. **模型特殊处理**

- ✅ **o1 系列**: 自动跳过不支持的参数（frequency_penalty, presence_penalty）
- ✅ **参数适配**: 根据模型类型自动调整 API 参数

### 6. **工具函数 (utils.py)**

新增实用函数：
- `estimate_cost()`: 估算 API 调用成本
- `format_messages_for_logging()`: 格式化消息用于日志
- `validate_config()`: 验证配置有效性

### 7. **日志记录**

- ✅ **调试日志**: 记录 API 调用详情
- ✅ **警告日志**: 记录重试和降级操作
- ✅ **错误日志**: 记录所有错误信息

## 📝 使用示例

### 基本使用

```python
from src.llm.factory import LLMFactory
from src.llm.base import LLMConfig

# 创建配置
config = LLMConfig(
    model_name="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
    max_retries=3  # 自动重试 3 次
)

# 创建 LLM 实例
llm = LLMFactory.create_llm(config)

# 生成响应
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]

response = llm.generate(messages)
print(response.content)
```

### 带重试的使用

```python
# 配置会自动处理重试
config = LLMConfig(
    model_name="gpt-4o",
    max_retries=5,  # 最多重试 5 次
    retry_delay=2.0  # 初始延迟 2 秒
)

llm = LLMFactory.create_llm(config)
# 如果遇到速率限制，会自动重试
response = llm.generate(messages)
```

### 流式生成

```python
# 流式生成响应
for chunk in llm.stream_generate(messages):
    print(chunk, end='', flush=True)
```

### Token 计数

```python
text = "Hello, world!"
token_count = llm.count_tokens(text)
print(f"Token count: {token_count}")
```

### 成本估算

```python
from src.llm.utils import estimate_cost

tokens = 1000
cost = estimate_cost(tokens, "gpt-4o")
print(f"Estimated cost: ${cost:.6f}")
```

## 🔧 配置选项说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_name` | str | 必需 | 模型名称（如 "gpt-4o", "o3-mini"） |
| `temperature` | float | 0.7 | 采样温度（0.0-2.0） |
| `max_tokens` | int | 2048 | 最大生成 token 数 |
| `top_p` | float | 1.0 | 核采样参数 |
| `frequency_penalty` | float | 0.0 | 频率惩罚 |
| `presence_penalty` | float | 0.0 | 存在惩罚 |
| `max_retries` | int | 3 | 最大重试次数 |
| `retry_delay` | float | 1.0 | 重试延迟（秒） |
| `timeout` | int | 60 | API 超时时间（秒） |

## 🚨 错误处理

### 自动重试的错误类型

1. **RateLimitError**: API 速率限制
   - 自动重试，使用指数退避
   
2. **APIConnectionError**: 网络连接错误
   - 自动重试，使用指数退避

3. **APIError**: 其他 API 错误
   - 不重试，直接抛出异常

### 错误示例

```python
try:
    response = llm.generate(messages)
except RateLimitError:
    print("速率限制，请稍后重试")
except APIConnectionError:
    print("网络连接错误")
except APIError as e:
    print(f"API 错误: {e}")
```

## 📊 支持的模型

### OpenAI 模型
- ✅ `gpt-4o`, `gpt-4`, `gpt-4-turbo`
- ✅ `gpt-3.5-turbo`
- ✅ `o1-preview`, `o1-mini`, `o3-mini`

### 未来支持
- ⏳ `vllm:*` - 本地 vLLM 模型
- ⏳ `ollama:*` - Ollama 本地模型

## 🔍 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 查看消息格式

```python
from src.llm.utils import format_messages_for_logging

formatted = format_messages_for_logging(messages)
print(formatted)
```

### 验证配置

```python
from src.llm.utils import validate_config

if validate_config(config):
    print("配置有效")
```

## 📈 性能优化建议

1. **合理设置 max_tokens**: 不要设置过大，避免浪费
2. **使用缓存**: 对于重复的请求，考虑实现缓存机制
3. **批量处理**: 如果可能，批量处理多个请求
4. **监控成本**: 使用 `estimate_cost()` 跟踪 API 使用成本

## 🐛 已知问题

1. **o1 系列限制**: o1 系列不支持 `frequency_penalty` 和 `presence_penalty`，已自动处理
2. **Token 计数**: 某些模型可能没有精确的 token 编码，会使用估算值

## 🔮 未来改进

- [ ] 实现请求缓存
- [ ] 支持批量请求
- [ ] 添加性能监控
- [ ] 实现 vLLM 客户端
- [ ] 实现 Ollama 客户端

