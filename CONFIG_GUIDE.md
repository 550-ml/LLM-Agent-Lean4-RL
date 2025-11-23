# 配置文件使用指南

## 📋 概述

本项目采用**配置文件优先**的设计原则，所有配置都集中在 `config/default.yaml` 文件中。尽量通过修改配置文件来调整参数，而不是使用命令行参数。

## 📁 配置文件结构

```yaml
# config/default.yaml

# 数据配置
data:
  benchmarks_dir: "data/benchmarks/lean4"  # 数据目录

# LLM 配置
llm:
  planning:      # 规划智能体配置
    model: "o3-mini"
    temperature: 0.7
    max_tokens: 2048
    # ... 更多参数
  
  generation:    # 生成智能体配置
    model: "gpt-4o"
    temperature: 0.7
    max_tokens: 2048
    # ... 更多参数

# Agent 配置
agent:
  max_retries: 5    # 最大重试次数
  timeout: 300      # 超时时间（秒）

# 验证器配置
verifier:
  lean_version: "4.24.0"
  project_path: "./lean_playground"
  timeout: 60
```

## 🎯 配置项说明

### 1. 数据配置 (`data`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `benchmarks_dir` | str | `"data/benchmarks/lean4"` | PutnamBench 数据目录 |

### 2. LLM 配置 (`llm`)

#### 规划智能体 (`llm.planning`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `model` | str | `"o3-mini"` | 模型名称 |
| `temperature` | float | `0.7` | 采样温度 |
| `max_tokens` | int | `2048` | 最大生成 token 数 |
| `top_p` | float | `1.0` | 核采样参数 |
| `frequency_penalty` | float | `0.0` | 频率惩罚 |
| `presence_penalty` | float | `0.0` | 存在惩罚 |
| `max_retries` | int | `3` | API 调用最大重试次数 |
| `retry_delay` | float | `1.0` | 重试延迟（秒） |
| `timeout` | int | `60` | API 超时时间（秒） |

#### 生成智能体 (`llm.generation`)

配置项与规划智能体相同，默认模型为 `"gpt-4o"`。

### 3. Agent 配置 (`agent`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_retries` | int | `5` | Agent 最大重试次数（验证失败后重新生成） |
| `timeout` | int | `300` | Agent 超时时间（秒） |

### 4. 验证器配置 (`verifier`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `lean_version` | str | `"4.24.0"` | Lean4 版本 |
| `project_path` | str | `"./lean_playground"` | Lean4 项目路径 |
| `timeout` | int | `60` | 验证超时时间（秒） |

## 🚀 使用方法

### 基本使用（使用默认配置）

```bash
# 列出所有问题
python main_putnam.py --list

# 处理单个问题
python main_putnam.py --file putnam_1962_a1.lean
```

### 使用自定义配置文件

```bash
# 创建自定义配置文件
cp config/default.yaml config/my_config.yaml

# 编辑 config/my_config.yaml，修改你需要的参数

# 使用自定义配置
python main_putnam.py --file putnam_1962_a1.lean --config config/my_config.yaml
```

### 在代码中使用

```python
from src.utils.config_manager import ConfigManager
from src.agent.coordinator import AgentCoordinator

# 加载配置管理器
config_manager = ConfigManager("config/default.yaml")

# 获取配置值
benchmarks_dir = config_manager.get_benchmarks_dir()
max_retries = config_manager.get_max_retries()
planning_model = config_manager.get("llm.planning.model")

# 创建协调器（自动从配置文件加载）
coordinator = AgentCoordinator.from_config(config_file="config/default.yaml")
```

## 📝 配置示例

### 示例 1: 使用更强大的模型

```yaml
llm:
  planning:
    model: "o1-preview"  # 使用更强的推理模型
    temperature: 0.5
  
  generation:
    model: "gpt-4-turbo"  # 使用更强的生成模型
    temperature: 0.8
    max_tokens: 4096
```

### 示例 2: 增加重试次数

```yaml
agent:
  max_retries: 10  # 增加重试次数，提高成功率

llm:
  planning:
    max_retries: 5  # LLM API 调用重试次数
  generation:
    max_retries: 5
```

### 示例 3: 使用测试数据

```yaml
data:
  benchmarks_dir: "data/test/lean4"  # 使用测试数据目录
```

### 示例 4: 调整温度参数

```yaml
llm:
  planning:
    temperature: 0.3  # 降低温度，更确定性的输出
  
  generation:
    temperature: 0.9  # 提高温度，更创造性的输出
```

## 🔧 配置优先级

1. **配置文件** (`config/default.yaml`) - 最高优先级
2. **环境变量** (如 `OPENAI_API_KEY`) - 覆盖配置文件中的 API key
3. **代码中的默认值** - 如果配置文件中没有，使用代码默认值

## 💡 最佳实践

1. **统一管理**: 所有配置都在 `config/default.yaml` 中
2. **版本控制**: 将配置文件加入版本控制，但不要提交包含 API key 的配置
3. **环境区分**: 为不同环境创建不同的配置文件（如 `config/dev.yaml`, `config/prod.yaml`）
4. **文档化**: 在配置文件中添加注释说明每个配置项的用途

## 🎨 配置文件模板

```yaml
# config/default.yaml
# 所有配置都在这里，尽量通过修改这个文件来调整参数

# 数据配置
data:
  benchmarks_dir: "data/benchmarks/lean4"

# LLM 配置
llm:
  planning:
    model: "o3-mini"
    temperature: 0.7
    max_tokens: 2048
    # ... 其他参数
  
  generation:
    model: "gpt-4o"
    temperature: 0.7
    max_tokens: 2048
    # ... 其他参数

# Agent 配置
agent:
  max_retries: 5
  timeout: 300

# 验证器配置
verifier:
  lean_version: "4.24.0"
  project_path: "./lean_playground"
  timeout: 60
```

## ❓ 常见问题

### Q: 如何切换模型？

A: 修改配置文件中的 `llm.planning.model` 和 `llm.generation.model`。

### Q: 如何调整重试次数？

A: 修改 `agent.max_retries`（Agent 重试）或 `llm.*.max_retries`（LLM API 重试）。

### Q: 如何切换数据目录？

A: 修改 `data.benchmarks_dir`。

### Q: 配置文件支持哪些格式？

A: 目前只支持 YAML 格式（`.yaml` 或 `.yml`）。

---

**记住**: 尽量通过修改配置文件来调整参数，而不是使用命令行参数！这样配置更统一、更易管理。

