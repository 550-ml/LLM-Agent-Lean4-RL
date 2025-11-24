# 快速开始指南

## 1. 环境准备

### 安装 Python 依赖

```bash
cd /home/wangtuo/WorkSpace/lean/LLM-Agent-Lean4-RL
pip install -r requirements.txt
```

### 设置 OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

或者创建 `.env` 文件：

```bash
cp .env.example .env
# 然后编辑 .env 文件，填入你的 API Key
```

### 安装 Lean4（如果未安装）

```bash
# 安装 Elan（Lean 版本管理器）
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh

# 安装 Lean 4
elan toolchain install 4.24.0

# 确保 lake 在 PATH 中
source ~/.elan/env
```

## 2. 运行测试示例

```bash
python example_test.py
```

这个示例会：
1. 使用一个简单的任务（identity 函数）
2. 创建协调器
3. 运行完整的规划-生成-验证流程
4. 输出生成的代码和证明

## 3. 使用命令行工具

如果你有任务目录（包含 `description.txt` 和 `task.lean`），可以这样运行：

```bash
python src/main.py --task-path /path/to/task_id_0
```

例如，使用 Lean4-LLM-Ai-Agent-Mooc 的任务：

```bash
python src/main.py --task-path /home/wangtuo/WorkSpace/lean/Lean4-LLM-Ai-Agent-Mooc/tasks/task_id_0
```

## 4. 在代码中使用

```python
from src.agent.coordinator import AgentCoordinator

# 创建协调器
coordinator = AgentCoordinator.from_config()

# 解决问题
result = coordinator.solve(
    problem_description="...",
    task_template="..."
)

print(result["code"])   # 生成的代码
print(result["proof"])  # 生成的证明
```

## 5. 自定义配置

你可以通过修改 `config/default.yaml` 或使用代码来配置：

```python
from src.agent.coordinator import AgentCoordinator
from src.llm.factory import LLMFactory
from src.llm.base import LLMConfig

# 自定义 LLM 配置
planning_config = LLMConfig(model_name="o3-mini", temperature=0.5)
generation_config = LLMConfig(model_name="gpt-4o", temperature=0.8)

planning_llm = LLMFactory.create_llm(planning_config)
generation_llm = LLMFactory.create_llm(generation_config)

# 创建协调器
coordinator = AgentCoordinator(
    planning_llm=planning_llm,
    generation_llm=generation_llm
)
```

## 6. 项目结构

```
LLM-Agent-Lean4-RL/
├── src/
│   ├── llm/          # LLM 模块
│   ├── agent/        # Agent 模块
│   ├── verifier/     # 验证模块
│   └── main.py       # 主入口
├── config/           # 配置文件
├── data/             # 数据目录
├── example_test.py   # 测试示例
└── requirements.txt  # 依赖
```

## 7. 常见问题

### Q: Lean 命令找不到？

A: 确保 Lean4 已安装，并且 `lake` 在 PATH 中：
```bash
which lake
# 如果找不到，运行：
source ~/.elan/env
```

### Q: API Key 错误？

A: 确保设置了 `OPENAI_API_KEY` 环境变量：
```bash
echo $OPENAI_API_KEY
```

### Q: 导入错误？

A: 确保在项目根目录运行，或者使用：
```python
import sys
sys.path.insert(0, "/path/to/LLM-Agent-Lean4-RL")
```

## 下一步

- 查看 [开发文档](./开发文档.md) 了解详细架构
- 查看 [项目结构](./PROJECT_STRUCTURE.md) 了解目录组织
- 尝试修改提示词和配置来优化性能

