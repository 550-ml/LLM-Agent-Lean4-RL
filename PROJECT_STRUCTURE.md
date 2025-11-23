# 项目结构说明

## 完整目录树

```
LLM-Agent-Lean4-RL/
├── README.md                    # 项目说明
├── 开发文档.md                  # 详细开发文档（本文件）
├── PROJECT_STRUCTURE.md         # 项目结构说明（本文件）
├── requirements.txt             # Python 依赖
├── pyproject.toml              # Python 项目配置
├── .gitignore                  # Git 忽略文件
├── .env.example                # 环境变量示例
│
├── config/                     # 配置文件目录
│   ├── default.yaml            # 默认配置
│   ├── llm_config.yaml         # LLM 配置
│   ├── agent_config.yaml       # Agent 配置
│   └── rl_config.yaml          # RL 配置（未来）
│
├── src/                        # 源代码目录
│   ├── __init__.py
│   │
│   ├── llm/                    # LLM 模块
│   │   ├── __init__.py
│   │   ├── base.py             # LLM 基础接口
│   │   ├── openai_client.py    # OpenAI 客户端
│   │   ├── vllm_client.py      # vLLM 本地模型客户端
│   │   ├── ollama_client.py    # Ollama 客户端（可选）
│   │   ├── factory.py          # LLM 工厂类
│   │   └── utils.py            # LLM 工具函数
│   │
│   ├── agent/                  # Agent 模块
│   │   ├── __init__.py
│   │   ├── base.py             # Agent 基类
│   │   ├── planning_agent.py   # 规划智能体
│   │   ├── generation_agent.py # 生成智能体
│   │   ├── verification_agent.py # 验证智能体
│   │   ├── coordinator.py      # 多智能体协调器
│   │   ├── state.py            # 状态管理
│   │   └── strategies.py       # 证明策略
│   │
│   ├── verifier/                # 形式化验证模块
│   │   ├── __init__.py
│   │   ├── lean4_runner.py     # Lean4 代码执行器
│   │   ├── error_parser.py     # 错误信息解析器
│   │   ├── state_tracker.py    # 证明状态跟踪器
│   │   └── repl_manager.py     # REPL 管理器（可选）
│   │
│   ├── rl/                      # RL 模块（未来）
│   │   ├── __init__.py
│   │   ├── environment.py      # RL 环境
│   │   ├── reward.py           # 奖励函数
│   │   ├── policy.py           # 策略网络
│   │   ├── trainer.py          # RL 训练器
│   │   ├── q_tree.py           # Q-tree 数据结构
│   │   └── utils.py            # RL 工具函数
│   │
│   ├── retrieval/              # RAG 模块（可选）
│   │   ├── __init__.py
│   │   ├── embedding_db.py     # 嵌入数据库
│   │   ├── embedding_models.py # 嵌入模型
│   │   └── retriever.py        # 检索器
│   │
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── logger.py           # 日志工具
│       ├── config_loader.py    # 配置加载器
│       └── file_utils.py       # 文件工具
│
├── data/                        # 数据目录
│   ├── benchmarks/             # 基准数据集
│   │   └── lean4/              # PutnamBench 数据集（已下载）
│   │       ├── src/
│   │       ├── README.md
│   │       └── ...
│   │
│   ├── prompts/                 # 提示词模板
│   │   ├── system/             # 系统提示词
│   │   │   ├── planning_agent.md
│   │   │   ├── generation_agent.md
│   │   │   └── verification_agent.md
│   │   └── user/               # 用户提示词模板
│   │
│   ├── cache/                   # 缓存目录
│   │   ├── llm_responses/      # LLM 响应缓存
│   │   └── embeddings/         # 嵌入向量缓存
│   │
│   └── logs/                    # 日志目录
│       ├── agent/              # Agent 日志
│       ├── verifier/           # 验证器日志
│       └── rl/                 # RL 日志（未来）
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_llm/               # LLM 模块测试
│   ├── test_agent/             # Agent 模块测试
│   ├── test_verifier/          # 验证器测试
│   └── integration/            # 集成测试
│
├── scripts/                     # 脚本目录
│   ├── setup.sh                # 环境设置脚本
│   ├── download_data.py       # 数据下载脚本
│   └── benchmark.py           # 基准测试脚本
│
├── docs/                        # 文档目录
│   ├── api/                    # API 文档
│   ├── tutorials/              # 教程
│   └── examples/               # 示例代码
│
└── lean_playground/            # Lean4 临时项目目录
    ├── lakefile.lean
    ├── lean-toolchain
    └── TempTest.lean           # 临时测试文件
```

## 关键文件说明

### 配置文件
- `config/default.yaml`: 主配置文件，包含所有模块的默认设置
- `config/llm_config.yaml`: LLM 特定配置（模型选择、API 密钥等）
- `config/agent_config.yaml`: Agent 配置（重试次数、超时等）

### 核心模块
- `src/llm/`: LLM 抽象层，支持多种后端
- `src/agent/`: 多智能体系统，实现规划-生成-验证流程
- `src/verifier/`: Lean4 代码执行和验证
- `src/rl/`: 强化学习模块（未来实现）

### 数据目录
- `data/benchmarks/lean4/`: PutnamBench 数据集
- `data/prompts/`: 提示词模板，用于指导 LLM 生成
- `data/cache/`: 缓存目录，提高性能
- `data/logs/`: 运行日志

### 测试
- `tests/`: 单元测试和集成测试
- 每个模块都有对应的测试目录

## 环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# LLM 配置
OPENAI_API_KEY=sk-...
VLLM_PORT=48000
OLLAMA_BASE_URL=http://localhost:11434

# Lean4 配置
LEAN_VERSION=4.24.0
LEAN_PROJECT_PATH=./lean_playground

# Agent 配置
MAX_RETRIES=5
TIMEOUT=300

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./data/logs
```

## 依赖管理

### requirements.txt 结构
```
# LLM 库
openai>=1.0.0
vllm>=0.6.0  # 可选，用于本地模型

# 工具库
pydantic>=2.0.0
pyyaml>=6.0
dataclasses-json>=0.6.0

# RL 库（未来）
# gymnasium>=0.29.0
# torch>=2.0.0
# stable-baselines3>=2.0.0

# 开发工具
pytest>=7.0.0
black>=23.0.0
mypy>=1.0.0
```

## 开发工作流

1. **添加新功能**:
   - 在对应模块目录下创建文件
   - 编写单元测试
   - 更新文档

2. **运行测试**:
   ```bash
   pytest tests/
   ```

3. **代码格式化**:
   ```bash
   black src/
   ```

4. **类型检查**:
   ```bash
   mypy src/
   ```

## 注意事项

1. **Lean4 版本**: 确保 Lean4 版本与数据集兼容
2. **API 密钥**: 不要将 API 密钥提交到版本控制
3. **缓存管理**: 定期清理 `data/cache/` 目录
4. **日志管理**: 日志文件可能很大，需要定期清理

