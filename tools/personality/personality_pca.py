import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def analyze_personality_pca(db_path: str):
    """
    使用主成分分析（PCA）对高维人格数据进行降维和可视化。

    方法:
    1.  将5维的人格数据进行“标准化”（Standardization），消除不同特征间的尺度差异。这是PCA的关键前置步骤。
    2.  应用PCA算法，找到数据中方差最大的两个正交方向，这被称为“主成分”（Principal Components）。
        这两个主成分可以被看作是新的、由原始5个特质线性组合而成的“超级特质”。
    3.  将所有数据点投影到这两个主成分构成的2D平面上。
    4.  生成一个2D散点图，其中每个点代表一次人格测试的结果。

    目的:
    PCA是一种强大的降维技术，它旨在用较少的维度来捕捉原始数据中尽可能多的信息（方差）。
    通过将5维数据可视化为2D散点图，我们可以直观地观察数据点的分布模式、聚集情况（是否存在聚类）以及是否存在异常值。
    这比一维的距离直方图提供了更丰富的数据结构信息。

    Args:
        db_path (str): Path to the SQLite database.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    # 1. 读取数据库中的personality数据
    with sqlite3.connect(db_path) as conn:
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

    # 2. 标准化数据 (PCA对特征的尺度很敏感)
    # 这是PCA的关键前置步骤，确保所有特征的权重相当
    scaler = StandardScaler()
    scaled_vectors = scaler.fit_transform(vectors)
    print("Data has been standardized (mean=0, variance=1) before applying PCA.")

    # 3. 执行PCA
    # 将5维数据降至2维
    pca = PCA(n_components=2)
    principal_components = pca.fit_transform(scaled_vectors)

    # 打印出每个主成分解释的方差比例
    explained_variance = pca.explained_variance_ratio_
    print(f"\nExplained variance by Principal Component 1: {explained_variance[0]:.2%}")
    print(f"Explained variance by Principal Component 2: {explained_variance[1]:.2%}")
    print(f"Total variance explained by 2 components: {np.sum(explained_variance):.2%}")
    print("This percentage represents how much of the original 5D information is captured in the 2D plot.")

    # 4. 创建2D散点图进行可视化
    plt.figure(figsize=(12, 8))
    plt.scatter(principal_components[:, 0], principal_components[:, 1], alpha=0.6, c='blue', edgecolors='k')
    
    plt.title('2D PCA of 5D Personality Data')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # 在窗口中显示图表
    print("\nAnalysis complete. Displaying PCA plot...")
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze personality data distribution using PCA.')
    parser.add_argument('--db-path', type=str, default='data/db/backup/samples300/deepseek-chat-single-1-300.db', help='Path to the SQLite database file.')
    
    args = parser.parse_args()
    
    analyze_personality_pca(args.db_path)
