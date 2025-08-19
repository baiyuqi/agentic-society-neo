import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
from scipy.stats import ttest_ind
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def load_personality_data(db_path: str) -> pd.DataFrame:
    """Loads personality data from the specified database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='personality';")
        if cursor.fetchone() is None:
            raise ValueError(f"Table 'personality' not found in database {db_path}")
        df = pd.read_sql_query("SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism FROM personality", conn)
    if df.empty:
        raise ValueError(f"The 'personality' table in {db_path} is empty.")
    return df

def compare_personalities(db_path1: str, db_path2: str):
    """
    对两个独立的人格画像实验数据集进行全面的比较分析。
    
    此脚本旨在回答一个核心问题：LLM生成的两个人格画像是否具有可识别性（Identifiability）？
    即，我们能否在统计上和视觉上将它们区分开来？

    分析分为两个层面：

    Part 1: 单变量分析 (Trait-by-Trait Comparison)
    -   逐一比较五个维度的人格特质。
    -   可视化: 使用并排的“小提琴图”(Violin Plots)来展示每个特质在两个样本中的分布形状、中位数和离散程度。
    -   统计检验: 使用“独立样本T检验”(T-test)来判断两个样本在每个特质上的均值差异是否具有统计显著性。

    Part 2: 多变量分析 (Holistic Profile Comparison)
    -   将每个测试结果作为一个5维向量，对两个向量“云”进行整体比较。
    -   可视化: 使用“主成分分析”(PCA)将全部600个数据点（2x300）投影到一个2D散点图上。
        如果两个画像是可识别的，我们应该能看到两个不同颜色的、清晰分离的数据簇。这是证明可识别性的最有力视觉证据。
    -   统计检验: 计算两个数据簇中心点之间的“马氏距离”(Mahalanobis Distance)。
        这是一个考虑了数据内部方差和相关性的高级距离度量，用一个数值来量化两个高维分布的“分离程度”。距离越大，可识别性越强。

    Args:
        db_path1 (str): 第一个人格画像的数据库路径。
        db_path2 (str): 第二个人格画像的数据库路径。
    """
    # Load data
    profile1_df = load_personality_data(db_path1)
    profile2_df = load_personality_data(db_path2)
    trait_columns = profile1_df.columns

    print("--- Part 1: Trait-by-Trait Comparison (Univariate Analysis) ---")

    # 1a. Visualization: Overlapping Violin Plots
    fig, axes = plt.subplots(1, len(trait_columns), figsize=(20, 6))
    fig.suptitle('Trait Distributions: Profile 1 vs. Profile 2', fontsize=16)
    
    combined_df = pd.concat([
        profile1_df.assign(Profile='Profile 1'),
        profile2_df.assign(Profile='Profile 2')
    ])

    for i, trait in enumerate(trait_columns):
        sns.violinplot(x='Profile', y=trait, data=combined_df, ax=axes[i], palette="muted")
        axes[i].set_title(trait.capitalize())
        axes[i].set_xlabel('')
        axes[i].set_ylabel('Score')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    print("Displaying Violin Plots for each trait...")
    plt.show()

    # 1b. Statistical Test: Independent Samples T-test
    print("\nIndependent Samples T-test Results (per trait):")
    print("A low p-value (e.g., < 0.05) suggests a statistically significant difference.")
    for trait in trait_columns:
        stat, p_value = ttest_ind(profile1_df[trait], profile2_df[trait])
        print(f"  - {trait.capitalize()}: t-statistic = {stat:.2f}, p-value = {p_value:.4f}")


    print("\n--- Part 2: Holistic Profile Comparison (Multivariate Analysis) ---")
    
    # 2a. Visualization: PCA Scatter Plot
    # Combine data and standardize
    all_vectors = np.vstack([profile1_df.values, profile2_df.values])
    scaler = StandardScaler()
    scaled_vectors = scaler.fit_transform(all_vectors)
    
    # Perform PCA
    pca = PCA(n_components=2)
    principal_components = pca.fit_transform(scaled_vectors)
    
    # Plot
    plt.figure(figsize=(12, 8))
    colors = ['#1f77b4', '#ff7f0e'] # Blue, Orange
    labels = ['Profile 1', 'Profile 2']
    
    # Plot Profile 1 points
    plt.scatter(principal_components[:len(profile1_df), 0], principal_components[:len(profile1_df), 1], 
                c=colors[0], label=labels[0], alpha=0.6)
    # Plot Profile 2 points
    plt.scatter(principal_components[len(profile1_df):, 0], principal_components[len(profile1_df):, 1], 
                c=colors[1], label=labels[1], alpha=0.6)

    plt.title('2D PCA of Personality Profiles')
    plt.xlabel(f'Principal Component 1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
    plt.ylabel(f'Principal Component 2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    print("\nDisplaying 2D PCA plot showing the separation of the two profile clouds...")
    plt.show()

    # 2b. Statistical Test: Mahalanobis Distance between group means
    mean1 = np.mean(profile1_df.values, axis=0)
    mean2 = np.mean(profile2_df.values, axis=0)
    
    # Pooled covariance matrix
    n1, n2 = len(profile1_df), len(profile2_df)
    cov1 = np.cov(profile1_df.values, rowvar=False)
    cov2 = np.cov(profile2_df.values, rowvar=False)
    pooled_cov = ((n1 - 1) * cov1 + (n2 - 1) * cov2) / (n1 + n2 - 2)
    
    try:
        inv_pooled_cov = np.linalg.inv(pooled_cov)
        delta_mean = mean1 - mean2
        mahalanobis_dist = np.sqrt(delta_mean.T @ inv_pooled_cov @ delta_mean)
        print(f"\nMahalanobis Distance between Profile 1 and Profile 2 means: {mahalanobis_dist:.2f}")
        print("A larger distance indicates greater separation between the two personality profiles.")
    except np.linalg.LinAlgError:
        print("\nCould not calculate Mahalanobis distance: Pooled covariance matrix is singular.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare two personality profile experiment datasets for identifiability.')
    parser.add_argument('--db1', type=str, default='data/db/backup/samples300/deepseek-chat-single-1-300.db', help='Path to the first profile database file.')
    parser.add_argument('--db2', type=str, default='data/db/backup/samples300/deepseek-chat-single-2-300.db', help='Path to the second profile database file.')
    
    args = parser.parse_args()
    
    compare_personalities(args.db1, args.db2)
