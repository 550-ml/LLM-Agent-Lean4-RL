# API Key 配置指南

本项目支持多种方式配置 API key，推荐使用环境变量方式（最安全）。

## 方式 1: 环境变量（推荐）⭐

### OpenAI API Key

在终端中设置环境变量：

```bash
# Linux/Mac
export OPENAI_API_KEY="sk-your-api-key-here"

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-api-key-here
```

**永久设置（Linux/Mac）**：
将以下内容添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

然后执行：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

### vLLM API Key（可选）

vLLM 通常不需要 API key，但如果你的 vLLM 服务器需要验证：

```bash
export VLLM_API_KEY="your-vllm-key"
export VLLM_BASE_URL="http://127.0.0.1:8000/v1"  # vLLM 服务器地址
```

## 方式 2: 配置文件

在 `config/default.yaml` 中添加 `api_key` 字段：

```yaml
llm:
  planning:
    model: "o3-mini"
    api_key: "sk-your-api-key-here"  # 添加这行
    temperature: 0.7
    max_tokens: 2048
    # ... 其他配置
  
  generation:
    model: "gpt-4o"
    api_key: "sk-your-api-key-here"  # 添加这行
    temperature: 0.7
    max_tokens: 2048
    # ... 其他配置
```

**注意**：不推荐将 API key 直接写在配置文件中，因为配置文件可能会被提交到版本控制系统。

## 方式 3: 代码中直接传递

在代码中创建 LLM 时直接传递：

```python
from src.llm import LLMFactory, LLMConfig

config = LLMConfig(
    model_name="gpt-4o",
    api_key="sk-your-api-key-here",  # 直接传递
    temperature=0.7,
    max_tokens=2048
)
llm = LLMFactory.create_llm(config)
```

## 优先级

API key 的读取优先级（从高到低）：
1. 代码中直接传递的 `api_key`
2. 配置文件中的 `api_key`
3. 环境变量 `OPENAI_API_KEY` 或 `VLLM_API_KEY`

## 验证配置

运行以下命令验证 API key 是否配置成功：

```bash
python -c "import os; print('✅ API Key 已设置' if os.getenv('OPENAI_API_KEY') else '❌ API Key 未设置')"
```

## 安全建议

1. **永远不要**将 API key 提交到 Git 仓库
2. 使用环境变量方式配置（最安全）
3. 如果必须使用配置文件，确保将配置文件添加到 `.gitignore`
4. 定期轮换 API key

