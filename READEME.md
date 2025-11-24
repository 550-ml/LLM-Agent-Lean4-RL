# 开发日记
11.24 
- 完成data数据加载
- 完成LLM类的构建，能从openai-api加载，并且通信，支持本地vLLM
- 完成lean4runner，能根据benckmark的环境进行lean4语言的验证
下一步：
- 完成Agent的开发，串起来这三个
  - 基础闭环
  - 多轮自我修复机制
  - 提示词：Agent = prompt + 结构化循环逻辑 + 状态管理 + 错误修复策略 + 搜索策略