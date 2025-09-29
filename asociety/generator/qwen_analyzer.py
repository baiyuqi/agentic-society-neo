import os
import base64
import io
from openai import OpenAI

# 使用在测试中验证过的固定配置
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-vl-plus" # 使用v-plus版本以支持视觉

def analyze_cluster_results(image_bytes, ari_score, profile_names):
    """
    使用千问多模态模型分析聚类结果。

    Args:
        image_bytes (bytes): 聚类结果图的字节数据 (PNG格式)。
        ari_score (float): 调整兰德指数 (ARI)。
        profile_names (list): 参与聚类的画像名称列表。

    Returns:
        str: 模型返回的分析文本。
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("环境变量 OPENAI_API_KEY 未设置。")

    client = OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)

    # 将图片字节转换为Base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # 构建详细的系统提示
    prompt = f"""
你是一位专业的数据科学家，你的任务是解读K-Means聚类分析的结果。
下面是一张PCA降维后的散点图和相应的“调整兰德指数”(ARI)。

**背景信息:**
- **目标**: 评估多个AI智能体画像的可区分性。我们想知道这些画像在性格测试结果上是否表现出独有的、可被算法识别的特征。
- **数据点**: 图中的每个点代表一个人物画像驱动的AI智能体的一次性格测试结果。实验中对每个智能体进行多次人物性格测试，每次测试形成一个点
- **点的形状 (True Profile)**: 代表这个智能体真实的来源画像文件。总共有 {len(profile_names)} 个不同的来源画像: {', '.join(profile_names)}.
- **点的颜色 (Predicted Cluster)**: 代表K-Means算法在不知道真实来源的情况下，将它分配到的簇。
- **调整兰德指数 (ARI)**: {ari_score:.4f}

**如何解读ARI:**
- ARI = 1.0: 完美匹配。算法找到的簇与真实来源完全对应，意味着画像之间**极易区分**。
- ARI ≈ 0.0: 随机分配。算法的聚类结果和瞎猜差不多，意味着画像**几乎无法区分**。
- ARI < 0.0: 比随机还差。

**你的任务:**
1.  **综合评估**: 根据ARI分数和图表，对这些画像的可区分性给出一个总体评价。
2.  **解读图表**: 详细描述图中的聚类情况。例如，哪些画像（形状）被很好地分开了？哪些画像被混在了一起？是否存在一个簇包含了多种不同来源的画像？
3.  **提出洞见**: 基于你的分析，提出可能的洞见或结论。例如，这是否说明模型在生成人格时具有多样性？或者说明模型生成的人格比较趋同？

请用清晰、结构化的方式给出你的分析。
"""

    try:
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"调用千问API时出错: {e}"

def save_figure_to_bytes(fig):
    """将 Matplotlib figure 保存到内存中的字节缓冲区 """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return buf.getvalue()

def analyze_image_with_text(image_bytes, prompt):
    """
    使用千问多模态模型，根据给定的prompt和图片进行分析。

    Args:
        image_bytes (bytes): 图片的字节数据 (PNG格式)。
        prompt (str): 指导模型进行分析的详细提示。

    Returns:
        str: 模型返回的分析文本。
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("环境变量 OPENAI_API_KEY 未设置。")

    client = OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)

    # 将图片字节转换为Base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    try:
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"调用千问API时出错: {e}"

