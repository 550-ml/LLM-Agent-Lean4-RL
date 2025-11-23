
示例:
  # 列出所有问题
  python main_putnam.py --list
  
  # 处理单个问题（使用默认配置）
  python main_putnam.py --file putnam_1962_a1.lean
  
  # 使用自定义配置文件
  python main_putnam.py --file putnam_1962_a1.lean --config config/custom.yaml
  
注意: 大部分配置都在 config/default.yaml 中，建议修改配置文件而不是使用命令行参数。
        """
# LLM-Agent-Lean4-RL

一个基于大语言模型的智能体系统，用于自动生成和验证 Lean4 形式化证明。

## 🎯 项目简介

本项目旨在构建一个完整的 LLM + Agent + Lean4 + RL 形式化证明框架，支持：

- 🤖 **多智能体协作**：规划、生成、验证三个智能体分工协作
- 🔌 **灵活的 LLM 支持**：支持本地模型（vLLM）和远程 API（OpenAI）
- ✅ **形式化验证**：自动执行和验证 Lean4 代码
- 🧠 **强化学习**：预留 RL 模块接口，支持未来优化证明策略

## 📚 文档

- **[开发文档](./开发文档.md)**: 详细的架构设计和实现指南
- **[项目结构](./PROJECT_STRUCTURE.md)**: 完整的项目目录结构说明

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd LLM-Agent-Lean4-RL

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Lean4（如果未安装）
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh
elan toolchain install 4.24.0
```

### 2. 配置

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，设置 API 密钥
# OPENAI_API_KEY=sk-...
```

### 3. 运行示例

```python
from src.llm.factory import LLMFactory
from src.llm.base import LLMConfig
from src.agent.coordinator import AgentCoordinator

# 创建 LLM
config = LLMConfig(model_name="gpt-4o", temperature=0.7)
llm = LLMFactory.create_llm(config)

# 创建智能体协调器
coordinator = AgentCoordinator.from_config(config)

# 解决问题
result = coordinator.solve(
    problem_description="...",
    task_template="..."
)
```

## 📦 项目结构

```
LLM-Agent-Lean4-RL/
├── src/              # 源代码
│   ├── llm/         # LLM 模块
│   ├── agent/       # Agent 模块
│   ├── verifier/    # 形式化验证模块
│   └── rl/          # RL 模块（未来）
├── data/            # 数据目录
│   ├── benchmarks/  # PutnamBench 数据集
│   └── prompts/     # 提示词模板
├── config/          # 配置文件
└── tests/           # 测试
```

详细结构请参考 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

## 🏗️ 架构设计

### 核心模块

1. **LLM 模块** (`src/llm/`)
   - 统一的 LLM 接口
   - 支持 OpenAI、vLLM、Ollama 等后端
   - 自动切换和负载均衡

2. **Agent 模块** (`src/agent/`)
   - 规划智能体：分析问题，制定策略
   - 生成智能体：生成代码和证明
   - 验证智能体：验证代码正确性
   - 协调器：管理多智能体协作

3. **形式化验证模块** (`src/verifier/`)
   - Lean4 代码执行器
   - 错误信息解析器
   - 证明状态跟踪器

4. **RL 模块** (`src/rl/`) - 未来实现
   - RL 环境定义
   - 奖励函数设计
   - 策略网络训练

### 工作流程

```
问题输入 → 规划智能体 → 生成智能体 → 验证智能体 → 输出结果
                ↓              ↓            ↓
             制定策略        生成代码     验证执行
                ↓              ↓            ↓
             迭代优化 ←─── 错误反馈 ←─── 错误分析
```

## 📊 数据集

项目使用 [PutnamBench](https://github.com/trishullab/PutnamBench) 数据集的 Lean4 部分，已下载到 `data/benchmarks/lean4/`。

## 🛠️ 技术栈

- **Python**: 3.10+
- **Lean4**: 4.24.0+
- **LLM**: OpenAI API, vLLM, Ollama
- **RL**: Gymnasium, PyTorch（未来）

## 📝 开发计划

### 阶段 1: 基础框架 ✅
- [x] 项目结构搭建
- [x] 开发文档编写
- [ ] LLM 模块实现
- [ ] Agent 模块实现

### 阶段 2: 核心功能
- [ ] 形式化验证模块
- [ ] RAG 支持
- [ ] 配置管理
- [ ] 日志系统

### 阶段 3: 优化与扩展
- [ ] 多智能体协作优化
- [ ] 错误恢复机制
- [ ] 性能优化

### 阶段 4: RL 模块（未来）
- [ ] RL 环境实现
- [ ] 策略网络训练
- [ ] 评估和对比

## 🤝 贡献

欢迎贡献！请参考 [开发文档](./开发文档.md) 了解详细的开发指南。

## 📄 许可证

[待定]

## 🙏 致谢

本项目参考了以下项目：
- [Lean4-LLM-Ai-Agent-Mooc](https://github.com/...): 多智能体架构参考
- [Lean_copra](https://github.com/...): RL 模块参考
- [PutnamBench](https://github.com/trishullab/PutnamBench): 数据集

## 📧 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

**最后更新**: 2025-01-XX  
**版本**: 0.1.0

