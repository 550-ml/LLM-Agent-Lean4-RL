#!/bin/bash

# 设置 HuggingFace 缓存目录（可选）
# export HF_HOME="/your/custom/cache/path"
# export TRANSFORMERS_CACHE="/your/custom/cache/path"

# 使用镜像站点（如果需要）
# export HF_ENDPOINT="https://hf-mirror.com"

python main.py --dir data/benchmarks/lean4/test