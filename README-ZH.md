# Agentic Society - 智能体社会模拟与分析平台

## 项目简介

Agentic Society 是一个用于创建、模拟和分析大规模智能体（Agent）社会的复杂系统。本项目的核心目标是探索当今的大语言模型（LLM）在多大程度上能够模拟真实人类社会的人格特质分布。

项目通过以下工作流程实现这一目标：

1.  **人口样本框架生成**: 基于人口普查数据（如年龄、性别、职业等统计分布），通过插值方法生成一个结构化的“人口骨架”（Population Skeleton）。
2.  **智能体画像丰富**: 利用大语言模型（LLM），将“人口骨架”中的基础信息丰富为具有详细背景、经历和生活细节的“智能体画像”（Agent Persona）。
3.  **人格特质测试**: 将生成的“智能体画像”作为背景信息（Prompt），让智能体完成标准的心理学人格问卷（如 IPIP-NEO）。
4.  **统计与分析**: 对智能体的人格测试结果进行深入的统计分析，并与真实世界的人类心理学研究数据进行比较，以评估 LLM 在模拟人格方面的能力和偏差。

## 系统结构

本系统主要由三部分组成：数据流水线、分析工具集和可视化工作室。

### 1. 数据流水线 (`tools/pipeline.py`)

这是项目的核心数据处理引擎，负责执行从“人口骨架”生成到“智能体画像”测试的全过程。它围绕一个“当前数据库”工作，该数据库记录了所有中间和最终数据。

-   **主要步骤**:
    1.  **初始化**: 创建并初始化一个新的数据库。
    2.  **抽样**: 根据人口普查数据生成样本骨架。
    3.  **丰富**: 调用 LLM API 将骨架丰富为画像。
    4.  **测试**: 使用画像作为输入，完成人格问卷。
    5.  **归档**: 完成流水线后，可将“当前数据库”备份为“历史数据库”，用于后续分析。

### 2. 分析工具集 (`tools/personality/`)

这是一组命令行工具，用于对“历史数据库”中的数据进行深入分析。

-   **主要功能**:
    -   **因子分析**: 评估人格问卷的结构效度。
    -   **内部一致性分析**: 检验问卷的信度。
    -   **群体比较**: 比较不同模型或不同群体的人格特质差异。
    -   **聚类与降维**: 使用 t-SNE、PCA 等方法对智能体人格进行可视化探索。

### 3. 可视化工作室 (`studio/`)

这是一个基于 Streamlit 的 Web 应用，提供了友好的图形化界面，用于：

-   **实时监控**: 可视化“当前数据库”中的画像生成和测试进度。
-   **数据探索**: 浏览、筛选和搜索已生成的智能体画像。
-   **交互式分析**: 运行与分析工具集类似的数据分析，并以图表形式展示结果。

## 核心概念

-   **人口骨架 (Skeleton)**: 仅包含人口统计学变量（如年龄、性别、教育、职业等）的基础样本。这是画像生成的起点。
-   **智能体画像 (Persona)**: 由 LLM 根据“骨架”信息扩展而来的丰富人物描述，包含详细的个人背景、生活故事、日常活动和性格特点。它是进行人格测试的直接输入。

## 使用指南

### 1. 安装依赖

本项目使用 [Poetry](https://python-poetry.org/) 进行依赖管理。请先确保已安装 Poetry。

```bash
# 克隆项目
git clone https://github.com/your-username/agentic-society.git
cd agentic-society

# 使用 Poetry 安装依赖
poetry install
```

### 2. 配置环境

在运行前，需要配置 LLM 的 API Key。请在项目根目录下创建 `.env` 文件，并填入以下内容：

```env
# 示例：使用 DeepSeek API
DEEPSEEK_API_KEY="your_deepseek_api_key"

# 示例：使用 OpenAI API
OPENAI_API_KEY="your_openai_api_key"
```

### 3. 运行数据流水线

数据流水线通过 `tools/pipeline.py` 脚本启动。这是一个命令行工具，你可以通过 `--help` 查看所有可用选项。

```bash
# 激活 Poetry 虚拟环境
poetry shell

# 查看流水线帮助信息
python -m tools.pipeline --help
```

**示例：完整运行一次流水线**

```bash
# 1. 初始化数据库（创建一个名为 my_experiment.db 的新数据库）
python -m tools.pipeline init --db-name my_experiment.db

# 2. 创建 100 个智能体骨架
python -m tools.pipeline sample --db-name my_experiment.db -n 100

# 3. 将骨架丰富为画像（使用 deepseek-chat 模型）
python -m tools.pipeline enrich --db-name my_experiment.db --model deepseek-chat

# 4. 对所有未测试的画像进行人格测试
python -m tools.pipeline elicit --db-name my_experiment.db --model deepseek-chat
```

### 4. 启动可视化工作室

可视化工作室是一个 Streamlit 应用，可以通过以下命令启动：

```bash
# 确保已在 Poetry 虚拟环境中
poetry shell

# 启动 Studio
streamlit run studio/agent-society-studio.py
```

启动后，浏览器将自动打开一个页面，你可以在其中选择要加载的数据库（包括“当前”和“历史”数据库），并进行交互式探索和分析。

## `tools` 目录工具介绍

-   `initialize_database.py`: 初始化一个新的 SQLite 数据库结构。
-   `create_persona_sample.py`: 从人口普查数据创建指定数量的“骨架”。
-   `generate_persona.py`: 调用 LLM 将“骨架”丰富为“画像”。
-   `load_ipip_set.py`: 将 IPIP-NEO 问卷题目加载到数据库中。
-   `pipeline.py`: 串联多个步骤的自动化数据流水线工具。
-   `inspect_db.py`: 一个简单的命令行工具，用于快速查看数据库内容。
-   `personality/`: 包含所有核心数据分析脚本的目录。
    -   `analyze_factor_structure.py`: 运行因子分析。
    -   `analyze_internal_consistency.py`: 计算克朗巴赫系数 (Cronbach's Alpha)。
    -   `compare_personalities.py`: 比较两组样本的人格均值。
    -   `personality_tsne.py`: 运行 t-SNE 降维并可视化。