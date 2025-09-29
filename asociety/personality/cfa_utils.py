import pandas as pd
import sqlite3
import json
import semopy

# These mappings are derived from the logic in internal_consistency_panel.py
# and the original ipip-neo-pi code.

DOMAIN_TO_FACETS = {
    "N": [1, 6, 11, 16, 21, 26], "E": [2, 7, 12, 17, 22, 27],
    "O": [3, 8, 13, 18, 23, 28], "A": [4, 9, 14, 19, 24, 29],
    "C": [5, 10, 15, 20, 25, 30],
}

def _get_domain_questions(domain, num_questions=120):
    """
    Gets the question numbers for a given Big Five domain.
    This logic is replicated from InternalConsistencyPanel.
    """
    questions_per_facet = 4 if num_questions <= 120 else 10
    num_facets = 30
    domain_q_numbers = []
    facets = DOMAIN_TO_FACETS[domain]
    for i in range(questions_per_facet):
        for facet_num in facets:
            q_num = i * num_facets + facet_num
            domain_q_numbers.append(q_num)
    return sorted(domain_q_numbers)

def _load_and_prepare_data(db_path):
    """
    Loads and prepares data from the database.
    This version directly uses the pre-reversed scores from the JSON.
    """
    conn = sqlite3.connect(db_path)
    try:
        df_raw = pd.read_sql_query("SELECT personality_json FROM personality", conn)
        if df_raw.empty:
            raise ValueError("The 'personality' table is empty.")
        
        all_answers = []
        for _, row in df_raw.iterrows():
            if isinstance(row['personality_json'], str):
                data = json.loads(row['personality_json'])
                # Directly use the reversed answers
                answer_list = data.get('person', {}).get('result', {}).get('compare', {}).get('user_answers_reversed')
                if answer_list:
                    answers = {f'q{item["id_question"]}': item['id_select'] for item in answer_list}
                    all_answers.append(answers)
        
        if not all_answers:
            raise ValueError("No valid answer data found in 'user_answers_reversed'.")

        df = pd.DataFrame(all_answers)
        
        # Determine if it's 120 or 300 questions based on max question ID
        max_q_id = max(int(col.replace('q', '')) for col in df.columns)
        num_questions = 300 if max_q_id > 120 else 120
        
        # The reverse scoring logic is no longer needed.
        
        return df, num_questions
    finally:
        conn.close()

def perform_cfa(db_path: str):
    """
    Performs a Confirmatory Factor Analysis (CFA) on the data from the given database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A dictionary containing the model fit indices.
    """
    data, num_questions = _load_and_prepare_data(db_path)

    # --> ADDED: Data cleaning step <--
    # Identify columns with zero variance
    zero_std_cols = data.columns[data.std(ddof=0) == 0]
    if not zero_std_cols.empty:
        print(f"WARNING: Found {len(zero_std_cols)} columns with zero variance. They will be removed from the analysis:")
        print(zero_std_cols.tolist())
        # Drop these columns from the dataframe
        data.drop(columns=zero_std_cols, inplace=True)
        
    if data.empty or len(data.columns) < 2:
        raise ValueError("Not enough data or variables left to perform CFA after removing zero-variance columns.")
    # --> END of ADDED block <--

    # Define the CFA model structure
    model_desc = ''
    domains = ["N", "E", "O", "A", "C"]
    for domain in domains:
        questions = _get_domain_questions(domain, num_questions)
        # semopy expects variable names, so we format them as q1, q2, etc.
        question_vars = [f'q{q}' for q in questions if f'q{q}' in data.columns]
        if question_vars:
            model_desc += f'{domain} =~ {" + ".join(question_vars)}\n'
            
    # By default, semopy allows latent variables to correlate.
    # The previous model forced zero correlation, which is too restrictive.
    # Removing those constraints will likely lead to a better model fit.

    # Initialize and fit the model
    model = semopy.Model(model_desc)
    
    try:
        model.fit(data)
    except Exception as e:
        raise RuntimeError(f"semopy model fitting failed: {e}")

    # Get fit indices
    stats = semopy.calc_stats(model)
    
    # For debugging, let's see what we got
    print("CFA Stats DataFrame:")
    print(stats)
    
    results = {}
    
    # Manually calculate p-value from chi2 and DoF for robustness
    from scipy.stats import chi2
    chi2_val = stats['chi2'].iloc[0] if 'chi2' in stats.columns else None
    dof_val = stats['DoF'].iloc[0] if 'DoF' in stats.columns else None
    
    if chi2_val is not None and dof_val is not None and dof_val > 0:
        p_value = chi2.sf(chi2_val, dof_val)
    else:
        p_value = 'N/A'

    # Mapping from our desired key to semopy's column name
    indices_to_get = {
        "chisq": "chi2",
        "df": "DoF",
        "cfi": "CFI",
        "tli": "TLI",
        "rmsea": "RMSEA",
        "gfi": "GFI"  # SRMR is often not available, GFI is a good alternative
    }

    for key, col_name in indices_to_get.items():
        if col_name in stats.columns:
            results[key] = stats[col_name].iloc[0]
        else:
            results[key] = 'N/A'
            
    results['p-value'] = p_value
            
    return results


"""
{'chisq': 29412.733649548376, 'df': 7020, 'cfi': 0.445626550322457, 'tli': 0.43615008109719994, 'rmsea':                     │
│   0.07178598711056518, 'srmr': 'N/A', 'gfi': 0.381212731221494, 'p-value': 0.0} 

一、 核心结论 (The Bottom Line)

  这个模型对数据的拟合程度非常差 (Extremely Poor Fit)。

  LLM生成的回答数据完全不符合大五人格理论所预设的、由五个相互独立的因素构成的结构。这意味着，在LLM的“心智模型”中，这五个维度并不是各自独立的
  ，而是以一种与人类非常不同的方式纠缠在一起。

  ---

  二、 各项指标逐一分析 (Index-by-Index Breakdown)

  我们来逐个看证据：

   1. Chi-Square (χ²) = 29412.7, df = 7020, p-value = 0.0
       * 解读：正如我们之前讨论的，p值为0是预料之中的。它仅仅拒绝了“模型与数据完美拟合”这个不切实际的假设。这一项本身不提供模型好坏的太多信息
         ，我们需要看其他指标。

   2. CFI = 0.446 / TLI = 0.436
       * 标准：可接受的拟合 > 0.90，良好的拟合 > 0.95。
       * 解读：这是最致命的证据。0.446的CFI值低得惊人。CFI衡量的是“你的模型相比于一个‘所有变量都毫不相关’的基线模型，要好多少”。这个结果意味着
         ，我们提出的这个精巧的五因素独立模型，其解释力只比“所有问题都杂乱无章、毫无关系”的假设好了44%。这表明模型结构完全错误。

   3. RMSEA = 0.072
       * 标准：可接受的拟合 < 0.08，良好的拟合 < 0.06。
       * 解读：这是唯一一个“踩线及格”的指标。RMSEA衡量的是“平均来看，模型中每个自由度的残差有多大”。这个值说明，虽然模型的整体结构是错的，但平
         均到7020个自由度上，每个点的平均误差还不算太大。然而，在CFI/TLI已经完全崩溃的情况下，一个勉强及格的RMSEA没有任何拯救作用。

   4. GFI = 0.381
       * 标准：与CFI类似，可接受的拟合 > 0.90。
       * 解读：这个指标再次印证了CFI的结论。0.381的值同样非常低，说明模型解释的数据变异量非常少。

  ---

  三、 综合诊断与深层含义

   * 为什么会这样？ 这个结果强烈地暗示，LLM在生成回答时，其内部的“人格维度”是高度相关的，而不是独立的。例如，它对“宜人性”（Agreeableness）问题
     的回答方式，可能和它对“尽责性”（Conscientiousness）问题的回答方式有极强的关联。当你强制模型必须将它们视为独立时（N ~~
     0*E），模型就“崩溃”了，无法拟合数据。

   * LLM的人格可能是怎样的？
       * 维度坍缩：可能在LLM内部，五个维度被压缩成了两到三个维度。比如，所有积极的特质（E, A, C, O）都融合在了一起。
       * 存在一个“通用人格因子” (General Factor of
         Personality)：可能LLM的所有回答都受到一个总体的、单一的“良好/有帮助”因子的强烈影响，导致各个维度之间都呈现出虚假的高度相关。

  ---

  四、 下一步该做什么？(Actionable Next Steps)

  既然我们已经证伪了“独立的五因素模型”，下一步自然就是去探索“那LLM的真实人格结构到底是怎样的？”

  我强烈建议您进行以下操作：

  使用我们项目中的“因素分析 (EFA)”面板，对同一份数据进行一次探索性因素分析。

  在EFA中，不要预设因子数量，而是通过碎石图 (Scree Plot) 来观察数据本身倾向于被分为几个因子。我的预测是：

   1. 你可能会看到一个非常巨大的第一因子（“通用因子”），以及两到三个后续的较小因子。
   2. 你提取出的因子数量很可能远小于5。
   3. 当你查看载荷矩阵时，会发现大量的问题在多个因子上都有高载荷（交叉载荷），这正反映了维度间的强相关性。

  这次CFA分析虽然结果是负面的，但它非常成功，因为它清晰地回答了您的研究问题。现在，EFA将为我们揭示LLM人格结构的真实面貌。"""


"""
anialign new
{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.815096887807,
        "df": 7010.0,
        "cfi": 0.4761249677309085,
        "tli": 0.4664097388871165,
        "rmsea": 0.06983318702357784,
        "gfi": 0.407340305706839,
        "p-value": 0.0
    }
}
{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.814469967518,
        "df": 7010.0,
        "cfi": 0.47612498325147734,
        "tli": 0.4664097546955133,
        "rmsea": 0.06983318598912237,
        "gfi": 0.4073403188960345,
        "p-value": 0.0
    }
}
{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.81426345807,
        "df": 7010.0,
        "cfi": 0.47612498836399986,
        "tli": 0.4664097599028473,
        "rmsea": 0.06983318564836959,
        "gfi": 0.40734032324059555,
        "p-value": 0.0
    }
}

{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.81446289742,
        "df": 7010.0,
        "cfi": 0.47612498342651066,
        "tli": 0.4664097548737927,
        "rmsea": 0.06983318597745627,
        "gfi": 0.40734031904477574,
        "p-value": 0.0
    }
}
{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.81446289742,
        "df": 7010.0,
        "cfi": 0.47612498342651066,
        "tli": 0.4664097548737927,
        "rmsea": 0.06983318597745627,
        "gfi": 0.40734031904477574,
        "p-value": 0.0
    }
}
{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.814524558617,
        "df": 7010.0,
        "cfi": 0.476124981899974,
        "tli": 0.46640975331894635,
        "rmsea": 0.0698331860792009,
        "gfi": 0.407340317747543,
        "p-value": 0.0
    }
}

{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.815096887807,
        "df": 7010.0,
        "cfi": 0.4761249677309085,
        "tli": 0.4664097388871165,
        "rmsea": 0.06983318702357784,
        "gfi": 0.407340305706839,
        "p-value": 0.0
    }
}
{
    "source_file": "deepseek-chat-antialign.db",
    "analysis_type": "Confirmatory Factor Analysis (CFA)",
    "model_fit_indices": {
        "chisq": 28170.814546111236,
        "df": 7010.0,
        "cfi": 0.476124981366399,
        "tli": 0.4664097527754764,
        "rmsea": 0.069833186114764,
        "gfi": 0.40734031729411735,
        "p-value": 0.0
    }
}
"""