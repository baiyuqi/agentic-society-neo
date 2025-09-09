helpcnstants = {
    'clustering': 
 {
    'zh': """
### 功能与用途

此工具使用 **K-Means 聚类算法**来**量化评估多个画像的可区分性**。

它将来自不同画像的所有数据点混合在一起，然后尝试将它们重新分成 K 个簇（K 等于画像的数量），完全不考虑它们的原始来源。最后，它通过**调整兰德指数 (ARI)** 来比较聚类结果与真实来源的一致性。

### 如何使用

1.  点击“浏览目录...”并选择一个包含多个 `.db` 文件的目录。
2.  点击“运行聚类”。
3.  分析完成后，下方表格会显示详细的分析指标。
4.  可以点击“拷贝数据 (JSON)”将分析指标复制到剪贴板。
5.  点击“结果解析”将图表和指标发送给AI进行解读。

### 如何解读结果

-   **调整兰德指数 (ARI)**:
    -   **ARI = 1.0**: 完美匹配。聚类算法找到的簇与原始的画像文件完全对应，意味着这些画像**极易区分**。
    -   **ARI ~= 0.0**: 随机分配。聚类结果与随机猜测无异，意味着这些画像**几乎无法区分**。
    -   **ARI < 0.0**: 比随机还差。

-   **PCA 散点图**:
    -   图上的每一个点代表一次性格测试结果。
    -   **点的颜色 (Predicted Cluster)**: 代表K-Means算法分配的簇。
    -   **点的形状 (True Profile)**: 代表它真实的来源文件。
    -   **理想情况**: 如果画像可区分性好，那么**相同形状的点应该具有相同的颜色**，并且在图上形成泾渭分明的色块。

-   **聚类中心距离 (Cluster Centroid Distances)**:
    -   **平均中心距离**: 所有聚类中心之间两两距离的平均值。这个值越大，说明所有画像在整体上的区分度越高。
    -   **距离矩阵**: 显示了每一对聚类中心之间的具体距离，可以用于分析哪些特定的画像更容易混淆。

### 核心算法介绍

-   **K-Means 聚类**: 一种简单高效的迭代式聚类算法。1) 随机选择K个点作为初始簇中心；2) 将每个数据点分配给离它最近的簇中心；3) 将每个簇的中心更新为该簇所有数据点的平均值；4) 重复步骤2和3，直到簇中心不再变化为止。
-   **调整兰德指数 (ARI)**: 它通过计算数据点对的“配对协议”来衡量聚类效果，并进行了“机会校正”，即减去了随机期望得到的分数。这使得它在不同大小和数量的簇之间具有可比性，非常可靠。
-   **主成分分析 (PCA)**: 一种线性的降维方法。它通过数学变换找到数据中方差最大的方向（第一主成分），然后是与前者正交的、方差次大的方向（第二主成分），以此类推。通过保留前两个主成分，我们可以在牺牲最少信息量的前提下，将高维数据投影到2D平面上进行可视化。
""",
    'en': """
### Function and Purpose

This tool uses **K-Means clustering algorithm** to **quantitatively assess the distinguishability of multiple profiles**.

It mixes all data points from different profiles together, then attempts to re-cluster them into K clusters (K equals the number of profiles), completely ignoring their original sources. Finally, it compares the clustering results with the true sources using the **Adjusted Rand Index (ARI)**.

### How to Use

1. Click "Browse Directory..." and select a directory containing multiple `.db` files.
2. Click "Run Clustering".
3. After analysis, the table below will show detailed analysis metrics.
4. Click "Copy Data (JSON)" to copy the analysis metrics to the clipboard.
5. Click "Analyze Results" to send the chart and metrics to an AI for interpretation.

### How to Interpret Results

-   **Adjusted Rand Index (ARI)**:
    -   **ARI = 1.0**: Perfect match. The clusters found by the algorithm correspond exactly to the original profile files, meaning these profiles are **highly distinguishable**.
    -   **ARI ~= 0.0**: Random assignment. The clustering result is no better than random guessing, meaning these profiles are **almost indistinguishable**.
    -   **ARI < 0.0**: Worse than random.

-   **PCA Scatter Plot**:
    -   Each point on the plot represents a personality test result.
    -   **Point Color (Predicted Cluster)**: Represents the cluster assigned by the K-Means algorithm.
    -   **Point Shape (True Profile)**: Represents its true source file.
    -   **Ideal Case**: If profiles have good distinguishability, then **points with the same shape should have the same color**, forming distinct color blocks on the plot.

-   **Cluster Centroid Distances**:
    -   **Average Centroid Distance**: The average of all pairwise distances between cluster centroids. A larger value indicates a higher overall distinguishability among all profiles.
    -   **Distance Matrix**: Shows the specific distance between each pair of cluster centroids, which can be used to analyze which specific profiles are more easily confused.

### Core Algorithm Introduction

-   **K-Means Clustering**: A simple and efficient iterative clustering algorithm. 1) Randomly select K points as initial cluster centers; 2) Assign each data point to the nearest cluster center; 3) Update each cluster center to the mean of all data points in that cluster; 4) Repeat steps 2 and 3 until cluster centers no longer change.
-   **Adjusted Rand Index (ARI)**: It measures clustering effectiveness by calculating "pairwise agreements" of data points and applies "chance correction" by subtracting the expected score from random assignment. This makes it comparable across different cluster sizes and numbers, making it very reliable.
-   **Principal Component Analysis (PCA)**: A linear dimensionality reduction method. It finds directions of maximum variance in the data through mathematical transformation (first principal component), then finds the orthogonal direction with the second largest variance (second principal component), and so on. By retaining the first two principal components, we can project high-dimensional data onto a 2D plane for visualization with minimal information loss.
"""
},
'comparison':{
    'zh': {
        'dist': """
### 功能与用途

此功能用于对一个目录下的**所有**画像进行**并排的、详细的视觉比较**。它能让您直观地检查每个画像在各个维度上的得分分布，以及它们在整体特征空间中的相对位置。

### 如何使用

1.  点击顶部的“选择目录...”按钮。
2.  点击“运行分布分析”。

### 如何解读结果

-   **小提琴图 (Violin Plots)**：上方的一排图表。每个小提琴图展示了一个画像在某个特定性格维度上的得分分布。您可以快速比较它们的形状、中位数和范围。
-   **PCA “云图”**：下方的大图。它将目录中**所有**画像的数据点都画在同一张图上，每个画像用一种颜色表示，用于直观评估所有画像的总体分离情况。

### 核心算法介绍

-   **小提琴图 (Violin Plot)**：它是**箱形图**与**核密度估计**的结合体，既能看到关键的统计摘要，又能看到数据的完整分布形状。
-   **PCA**：一种线性的降维方法，通过找到数据中方差最大的方向来将高维数据投影到2D平面上进行可视化。
""",
        'heatmap': """
### 功能与用途

此功能提供了一种**快速、量化地概览一个目录中所有画像对之间可区分性**的方法。它计算每一对画像之间的**马氏距离**，并用一个**热力图 (Heatmap)** 来展示结果。

### 如何使用

1.  点击顶部的“选择目录...”按钮。
2.  点击“生成热力图”。

### 如何解读结果

-   这是一个对称的矩阵，行和列都是目录中的文件名。
-   单元格的**数值和颜色**代表了对应行列两个画像之间的马氏距离。
-   **距离越大（颜色越亮/越“热”）**，代表这两个画像在多维特征空间中的中心点相距越远，它们的**可区分性越强**。
-   **距离越小（颜色越暗/越“冷”）**，代表这两个画像越**相似，越难以区分**。

### 核心算法介绍

-   **群体间马氏距离**：当计算两个数据**群体**之间的马氏距离时，我们实际上是在计算两个群体**均值向量**之间的距离。这里的关键是使用一个**池化协方差矩阵 (Pooled Covariance Matrix)**，它是两个群体协方差矩阵的加权平均值，这提供了一个更稳健、更准确的对两个群体共同的方差结构的估计。
"""
    },
    'en': {
        'dist': """
### Function and Purpose

This feature is used for **side-by-side, detailed visual comparison** of **all** profiles in a directory. It allows you to intuitively examine the score distribution of each profile across various dimensions and their relative positions in the overall feature space.

### How to Use

1. Click the "Select Directory..." button at the top.
2. Click "Run Distribution Analysis".

### How to Interpret Results

- **Violin Plots**: The row of charts at the top. Each violin plot shows the score distribution of a profile on a specific personality dimension. You can quickly compare their shapes, medians, and ranges.
- **PCA "Cloud Plot"**: The large chart at the bottom. It plots **all** profile data points on the same chart, with each profile represented by a color, for intuitive assessment of overall separation among all profiles.

### Core Algorithm Introduction

- **Violin Plot**: A combination of **box plot** and **kernel density estimation**, showing both key statistical summaries and complete distribution shapes.
- **PCA**: A linear dimensionality reduction method that projects high-dimensional data onto a 2D plane for visualization by finding directions of maximum variance in the data.
""",
        'heatmap': """
### Function and Purpose

This feature provides a **quick, quantitative overview of the distinguishability between all profile pairs** in a directory. It calculates the **Mahalanobis distance** between each pair of profiles and displays the results using a **Heatmap**.

### How to Use

1. Click the "Select Directory..." button at the top.
2. Click "Generate Heatmap".

### How to Interpret Results

- This is a symmetric matrix where rows and columns are filenames in the directory.
- The **values and colors** in cells represent the Mahalanobis distance between corresponding row and column profiles.
- **Larger distances (brighter/hotter colors)** indicate that the two profiles are farther apart in the multidimensional feature space, meaning **stronger distinguishability**.
- **Smaller distances (darker/cooler colors)** indicate that the profiles are more **similar and harder to distinguish**.

### Core Algorithm Introduction

- **Inter-group Mahalanobis Distance**: When calculating Mahalanobis distance between two data **groups**, we actually compute the distance between the **mean vectors** of the two groups. The key is using a **Pooled Covariance Matrix**, which is a weighted average of the covariance matrices of the two groups, providing a more robust and accurate estimate of the common variance structure of both groups.
"""
    }
},
'factor_analysis': {
    'zh': {
        'title': "探索性因素分析 (EFA)",
        'content': """
### 功能与用途
探索性因素分析 (EFA) 是一种统计方法，用于**识别一组观测变量背后的潜在结构**（即“因素”）。在性格问卷的背景下，它帮助我们验证这120或300个问题是否真的能有效地衡量预设的“大五”人格特质。

### 如何使用
1.  点击“选择数据库文件...”并选择一个包含 `personality` 表的 `.db` 文件。
2.  点击“运行因素分析”。

### 如何解读结果
-   **数据充分性检验**:
    -   **KMO检验**: 衡量数据的抽样充分性。值 > 0.6 通常被认为是可接受的。
    -   **Bartlett球形检验**: 检验变量之间是否存在相关性。如果 **p值 < 0.05**，则表明数据适合进行因素分析。
-   **碎石图 (Scree Plot)**:
    -   用于帮助决定要提取多少个因素。
    -   寻找图中山势变缓的“拐点”(Elbow)。“拐点”之前的因素数量通常是理想的提取数量。根据“大五”理论，我们期望看到5个主要因素。
-   **因素载荷热图 (Factor Loadings Heatmap)**:
    -   显示了每个问题（Y轴）在每个提取出的因素（X轴）上的“载荷”或“权重”。
    -   一个深色（或亮色，取决于颜色方案）的单元格表示该问题与该因素高度相关。
    -   **理想情况**: 每个问题应该只在一个因素上有高载荷，这表明问卷具有良好的“简单结构”，每个问题都明确地指向一个特定的人格特质。

### 核心算法介绍
EFA通过分析变量间的相关性矩阵来提取因素。它假设每个观测变量都是各个潜在因素的线性组合，并旨在找到能最好地解释变量间相关性的因素。**Varimax旋转**是一种常用的“正交旋转”方法，它能使因素载荷矩阵的列变得“更简单”（即，让每个变量只在一个因素上有高载荷），从而使结果更容易解释。
"""
    },
    'en': {
        'title': "Exploratory Factor Analysis (EFA)",
        'content': """
### Function and Purpose
Exploratory Factor Analysis (EFA) is a statistical method used to **identify the underlying structure** (i.e., "factors") behind a set of observed variables. In the context of a personality questionnaire, it helps us verify if the 120 or 300 questions are indeed effectively measuring the intended "Big Five" personality traits.

### How to Use
1.  Click "Select Database File..." and choose a `.db` file containing a `personality` table.
2.  Click "Run Factor Analysis".

### How to Interpret Results
-   **Data Adequacy Checks**:
    -   **KMO Test**: Measures the sampling adequacy. A value > 0.6 is generally considered acceptable.
    -   **Bartlett's Test of Sphericity**: Tests if there are correlations among the variables. A **p-value < 0.05** indicates that the data is suitable for factor analysis.
-   **Scree Plot**:
    -   Used to help decide how many factors to extract.
    -   Look for the "elbow" where the slope of the graph levels off. The number of factors before the elbow is often the ideal number to extract. Based on the Big Five theory, we expect to see 5 major factors.
-   **Factor Loadings Heatmap**:
    -   Shows the "loading" or "weight" of each question (Y-axis) on each extracted factor (X-axis).
    -   A dark (or light, depending on the color scheme) cell indicates that the question is highly correlated with that factor.
    -   **Ideal Case**: Each question should have a high loading on only one factor, indicating that the questionnaire has a good "simple structure," where each question clearly points to a specific personality trait.

### Core Algorithm Introduction
EFA extracts factors by analyzing the correlation matrix of the variables. It assumes that each observed variable is a linear combination of various underlying factors and aims to find the factors that best explain the correlations among the variables. **Varimax rotation** is a common "orthogonal rotation" method that simplifies the columns of the factor loading matrix, making each variable load highly on only one factor, thus making the results easier to interpret.
"""
    }
},
'tsne': {
    'zh': """
### 功能与用途

t-SNE 是一种强大的**非线性降维技术**，非常擅长将高维数据（如5维的性格向量）投影到2D平面上，同时尽可能保持其局部的相似性结构。

它纯粹用于**可视化探索**，帮助您直观地观察不同画像的数据点在空间中是如何分布和分离的。

### 如何使用

1.  点击“浏览目录...”并选择一个包含多个 `.db` 文件的目录。
2.  点击“运行 t-SNE”。

### 如何解读结果

-   图上的每一个点代表一次性格测试结果，颜色代表其来源文件。
-   **理想情况**：如果多个画像是高度可区分的，那么在t-SNE图上，**相同颜色的点会自然地聚集在一起，形成清晰、分离的“岛屿”或“大陆”**。
-   **混合情况**：如果不同颜色的点大量重叠、混合在一起，则说明这些画像在特征空间中非常相似，难以区分。

### 核心算法介绍

**t-分布随机邻域嵌入 (t-SNE)**：它的工作方式很精妙。

首先，它在原始高维空间中，将数据点之间的欧氏距离转化为一个条件概率，表示点A会选择点B作为其邻居的可能性（距离越近，概率越高）。

然后，它在低维空间（如2D）中也定义一个类似的概率分布（使用更“重尾”的t分布，以缓解“拥挤问题”）。

最后，它通过优化算法，不断调整低维空间中各点的位置，使得两个空间的概率分布尽可能地相似。这个过程保留了数据的局部“邻居”关系，因此非常擅长可视化高维数据的内在流形结构。

**注意**：t-SNE图上簇与簇之间的距离大小不一定具有真实的数学意义，应主要关注点簇的形成和分离情况。
""",
    'en': """
### Function and Purpose

t-SNE is a powerful **nonlinear dimensionality reduction technique** that excels at projecting high-dimensional data (such as 5-dimensional personality vectors) onto a 2D plane while preserving local similarity structures as much as possible.

It is purely used for **visualization exploration**, helping you intuitively observe how data points from different profiles are distributed and separated in space.

### How to Use

1. Click "Browse Directory..." and select a directory containing multiple `.db` files.
2. Click "Run t-SNE".

### How to Interpret Results

- Each point on the plot represents a personality test result, with color representing its source file.
- **Ideal Case**: If multiple profiles are highly distinguishable, then on the t-SNE plot, **points of the same color will naturally cluster together, forming clear, separated "islands" or "continents"**.
- **Mixed Case**: If points of different colors heavily overlap and mix together, it indicates that these profiles are very similar in the feature space and difficult to distinguish.

### Core Algorithm Introduction

**t-Distributed Stochastic Neighbor Embedding (t-SNE)**: Its working mechanism is quite sophisticated.

First, in the original high-dimensional space, it converts Euclidean distances between data points into conditional probabilities, representing the likelihood that point A would choose point B as its neighbor (closer distance means higher probability).

Then, it defines a similar probability distribution in the low-dimensional space (such as 2D) using a "heavier-tailed" t-distribution to alleviate the "crowding problem".

Finally, through optimization algorithms, it continuously adjusts the positions of points in the low-dimensional space to make the probability distributions of the two spaces as similar as possible. This process preserves the local "neighbor" relationships of the data, making it excellent at visualizing the intrinsic manifold structure of high-dimensional data.

**Note**: The distances between clusters on a t-SNE plot do not necessarily have real mathematical meaning; focus should be on cluster formation and separation.
"""
},
'mahalanobis':  {
    'zh': """
### 功能与用途

此工具用于评估**单个画像的内部一致性与分布形态**. 它计算该画像中每一个数据点（即每一次性格测试的结果）到整个数据集中心点的马氏距离.

-   如果一个画像是**高度一致和集中的**，那么大部分数据点的马氏距离都会很小，分布会很紧凑.
-   如果画像**松散或包含异常点**，则距离分布会更分散.

### 如何使用

1.  点击“选择文件...”按钮，选择一个您想要分析的 `.db` 文件.
2.  点击“运行分析”按钮，面板会自动生成并显示一个直方图.
3.  点击“拷贝数据 (JSON)”按钮，将表格中的数据以JSON格式复制到剪贴板.

### 如何解读结果

-   **横轴 (X-axis)**: 马氏距离的值.
-   **纵轴 (Y-axis)**: 拥有该距离值的数据点数量或概率密度.
-   **理想形态**: 一个理想的、内部一致的画像通常会呈现一个**右偏（positively skewed）**的分布. 即，大部分数据点聚集在左侧（距离小），只有少数点离中心较远.
-   **异常形态**: 如果直方图呈现双峰、均匀分布或有非常长的尾巴，则可能意味着该画像内部存在不一致、包含多个子群体或有极端异常值.

### 核心算法介绍

**马氏距离 (Mahalanobis Distance)**: 它为何优于我们熟悉的欧氏距离（两点直线距离）？

马氏距离考虑了两个重要因素:
1.  **尺度无关**: 它用标准差对每个维度进行归一化，消除了不同维度量纲的影响.
2.  **维度间相关性**: 它使用协方差矩阵来考虑维度间的相关性.

因此，它度量的是一个点到数据中心的“统计学距离”，是多维数据**异常检测**的黄金标准.
""",
    'en': """
### Function and Purpose

This tool is used to assess the **internal consistency and distribution pattern of a single profile**. It calculates the Mahalanobis distance from each data point (i.e., each personality test result) in the profile to the center of the entire dataset.

- If a profile is **highly consistent and concentrated**, most data points will have small Mahalanobis distances, and the distribution will be compact.
- If the profile is **loose or contains outliers**, the distance distribution will be more dispersed.

### How to Use

1. Click the "Browse File..." button and select a `.db` file you want to analyze.
2. Click the "Run Analysis" button, and the panel will automatically generate and display a histogram.
3. Click the "Copy Data (JSON)" button to copy the data from the table to the clipboard in JSON format.

### How to Interpret Results

- **X-axis**: Mahalanobis distance values.
- **Y-axis**: Number of data points or probability density with that distance value.
- **Ideal Pattern**: An ideal, internally consistent profile typically shows a **positively skewed** distribution. That is, most data points cluster on the left side (small distances), with only a few points far from the center.
- **Abnormal Pattern**: If the histogram shows bimodal, uniform distribution, or very long tails, it may indicate internal inconsistency, multiple subgroups, or extreme outliers within the profile.

### Core Algorithm Introduction

**Mahalanobis Distance**: Why is it superior to the familiar Euclidean distance (straight-line distance between two points)?

Mahalanobis distance considers two important factors:
1. **Scale-invariant**: It normalizes each dimension using standard deviation, eliminating the influence of different dimensional scales.
2. **Inter-dimensional correlation**: It uses the covariance matrix to account for correlations between dimensions.

Therefore, it measures the "statistical distance" from a point to the data center and is the gold standard for **anomaly detection** in multidimensional data.
"""
},
'internal_consistency': {
    'zh': {
        'title': "内部一致性信度分析 (Cronbach's Alpha)",
        'content': """
### 功能与用途
该工具用于评估一组测试题项在多大程度上测量了同一个潜在构念（例如，“外向性”）。**Cronbach's Alpha (α)** 是衡量这种内部一致性的最常用指标。

### 如何使用
1.  点击“选择数据库文件...”并选择一个包含 `personality` 表的 `.db` 文件。
2.  点击“运行分析”。

### 如何解读结果
-   **Cronbach's Alpha (α) 值**:
    -   **α ≥ 0.9**: 非常优秀 (Excellent)
    -   **0.8 ≤ α < 0.9**: 良好 (Good)
    -   **0.7 ≤ α < 0.8**: 可接受 (Acceptable)
    -   **0.6 ≤ α < 0.7**: 有问题 (Questionable)
    -   **0.5 ≤ α < 0.6**: 差 (Poor)
    -   **α < 0.5**: 不可接受 (Unacceptable)
-   图表中的虚线表示 **0.7**，这是心理测量学中普遍接受的最低标准。

### 核心算法介绍
Cronbach's Alpha (α) 基于测试中所有题项的平均相关性。它的计算考虑了测试的题项数量和题项间的平均协方差。一个高α值表明，测试中的所有题项似乎都在一致地测量同一个东西。
"""
    },
    'en': {
        'title': "Internal Consistency Reliability (Cronbach's Alpha)",
        'content': """
### Function and Purpose
This tool assesses the extent to which a set of test items measures the same underlying construct (e.g., "Extraversion"). **Cronbach's Alpha (α)** is the most common metric for this internal consistency.

### How to Use
1.  Click "Select Database File..." and choose a `.db` file containing a `personality` table.
2.  Click "Run Analysis".

### How to Interpret Results
-   **Cronbach's Alpha (α) Value**:
    -   **α ≥ 0.9**: Excellent
    -   **0.8 ≤ α < 0.9**: Good
    -   **0.7 ≤ α < 0.8**: Acceptable
    -   **0.6 ≤ α < 0.7**: Questionable
    -   **0.5 ≤ α < 0.6**: Poor
    -   **α < 0.5**: Unacceptable
-   The dashed line on the chart at **0.7** represents the generally accepted minimum standard in psychometrics.

### Core Algorithm Introduction
Cronbach's Alpha (α) is based on the average correlation of all items in a test. Its calculation considers the number of items and the average inter-item covariance. A high α value indicates that all items in the test appear to be consistently measuring the same thing.
"""
    }
}
}