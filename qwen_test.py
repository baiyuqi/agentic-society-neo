import os
import sys
import argparse
from openai import OpenAI

def test_qwen_model():


    # --- Configuration ---
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name = "qwen-plus"

    # --- Variable Check ---
    if not all([api_key, base_url, model_name]):
        print("错误：请确保已设置 API Key、Base URL 和模型名称。", file=sys.stderr)
        if not api_key:
            print(" - 环境变量 OPENAI_API_KEY 未设置。", file=sys.stderr)
        if not base_url:
            print(" - 环境变量 OPENAI_BASE_URL 未设置，且未通过 --base-url 提供。", file=sys.stderr)
        if not model_name:
            print(" - 环境变量 OPENAI_MODEL 未设置。", file=sys.stderr)
        sys.exit(1)

    print("测试配置:")
    print(f"  - Base URL: {base_url}")
    print(f"  - Model: {model_name}")
    print("-" * 20)

    # --- Client Initialization ---
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        print(f"初始化 OpenAI 客户端时出错: {e}", file=sys.stderr)
        sys.exit(1)

    # --- API Call ---
    try:
        print("正在发送请求...")
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "你好，请介绍一下你自己。"}],
            model=model_name,
        )
        print("请求成功！")
        print("-" * 20)
        print("模型回复:")
        print(chat_completion.choices[0].message.content)

    except Exception as e:
        print(f"调用 API 时出错: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_qwen_model()