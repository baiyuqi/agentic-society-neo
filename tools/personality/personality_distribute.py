import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os

def analyze_personality_distribution(db_path: str):
    """
    使用欧几里得距离分析人格向量的分布。

    方法:
    1. 将每个5维的人格特质向量视为高维空间中的一个点。
    2. 计算所有这些点的算术平均值，得到一个“平均人格向量”。
    3. 计算每个点到这个中心点的欧几里得距离（即直线距离）。
    4. 绘制这些距离值的分布直方图。

    目的:
    此方法旨在通过将高维信息压缩为一维的距离值，来观察人格测试结果的“离散程度”或“稳定性”。
    直方图可以显示大多数测试结果是紧密聚集在平均值附近，还是广泛地散布开来。

    局限性:
    欧几里得距离虽然直观，但它将所有维度同等对待，且忽略了各维度之间的相关性。
    这可能导致对数据结构的理解过于简化。对于更深入的分析，PCA或马氏距离可能是更好的选择。

    Args:
        db_path (str): Path to the SQLite database.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    # 1. 读取数据库中的personality数据
    with sqlite3.connect(db_path) as conn:
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='personality';")
        if cursor.fetchone() is None:
            raise ValueError(f"Table 'personality' not found in database {db_path}")
            
        df = pd.read_sql_query("SELECT persona_id, openness, conscientiousness, extraversion, agreeableness, neuroticism FROM personality", conn)

    if df.empty:
        print("The 'personality' table is empty. No analysis to perform.")
        return

    trait_columns = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    vectors = df[trait_columns].values

    # 2. 计算均值向量
    mean_vector = np.mean(vectors, axis=0)
    print(f"Mean Vector: {mean_vector}")

    # 3. 计算所有向量与均值向量的欧几里得距离
    distances = np.linalg.norm(vectors - mean_vector, axis=1)
    df['distance_to_mean'] = distances
    
    print("\nSample of calculated distances:")
    print(df[['persona_id', 'distance_to_mean']].head())

    # 4. 计算每个区间的样本个数并可视化距离的概率分布
    
    # 首先，使用 np.histogram 计算获得原始计数和区间边界
    counts, bin_edges = np.histogram(distances, bins='auto')
    
    print("\nSample counts per bin:")
    for i in range(len(counts)):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i+1]
        count = counts[i]
        print(f"  Bin [{bin_start:.2f} - {bin_end:.2f}]: {count} samples")

    # 然后，使用计算好的区间边界来绘制概率密度图
    plt.figure(figsize=(10, 6))
    plt.hist(distances, bins=bin_edges, density=True, alpha=0.7, color='blue', edgecolor='black')
    
    plt.title('Probability Distribution of Euclidean Distances from Mean Personality Vector')
    plt.xlabel('Euclidean Distance')
    plt.ylabel('Probability Density')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # 在窗口中显示图表
    print("\nAnalysis complete. Displaying plot...")
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze and visualize the distribution of personality traits.')
    parser.add_argument('--db-path', type=str, default='data/db/backup/deepseek-chat-single-1-300.db', help='Path to the SQLite database file.')
    
    args = parser.parse_args()
    
    analyze_personality_distribution(args.db_path)