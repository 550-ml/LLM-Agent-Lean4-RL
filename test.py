# test_api_key.py (放在项目根目录)


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_api_key():
    """测试 API key 是否配置正确"""
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 OPENAI_API_KEY 环境变量")
        print("请运行: export OPENAI_API_KEY='sk-your-key'")
        return False

    print(f"✅ 检测到 API Key: {api_key[:10]}...")

    from src.llm import LLMFactory, LLMConfig
    # 尝试创建 LLM 实例
    try:
        config = LLMConfig(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100
        )
        llm = LLMFactory.create_llm(config)
        print("✅ LLM 实例创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建 LLM 实例失败: {e}")
        return False


if __name__ == "__main__":
    print("开始测试 API key 是否配置正确...")
    test_api_key()
