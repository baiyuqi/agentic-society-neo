library(readr)
library(dplyr)
library(psych)
library(corrplot)

# 1. 读取 CSV 文件
ipip_data <- read_csv("d:/answers.csv")

# 2. 计算五大人格维度平均分（对应题号）
ipip_scores <- ipip_data %>%
  mutate(
    N = rowMeans(select(., I1, I31, I61, I91,
                           I6, I36, I66, I96,
                           I11, I41, I71, I101,
                           I16, I46, I76, I106,
                           I21, I51, I81, I111,
                           I26, I56, I86, I116), na.rm = TRUE),
    E = rowMeans(select(., I2, I32, I62, I92,
                           I7, I37, I67, I97,
                           I12, I42, I72, I102,
                           I17, I47, I77, I107,
                           I22, I52, I82, I112,
                           I27, I57, I87, I117), na.rm = TRUE),
    O = rowMeans(select(., I3, I33, I63, I93,
                           I8, I38, I68, I98,
                           I13, I43, I73, I103,
                           I18, I48, I78, I108,
                           I23, I53, I83, I113,
                           I28, I58, I88, I118), na.rm = TRUE),
    A = rowMeans(select(., I4, I34, I64, I94,
                           I9, I39, I69, I99,
                           I14, I44, I74, I104,
                           I19, I49, I79, I109,
                           I24, I54, I84, I114,
                           I29, I59, I89, I119), na.rm = TRUE),
    C = rowMeans(select(., I5, I35, I65, I95,
                           I10, I40, I70, I100,
                           I15, I45, I75, I105,
                           I20, I50, I80, I110,
                           I25, I55, I85, I115,
                           I30, I60, I90, I120), na.rm = TRUE)
  ) %>%
  select(N, E, O, A, C)

# 3. 计算相关矩阵及显著性检验
corr_res <- corr.test(ipip_scores, use = "pairwise")

print(corr_res$r)       # 相关系数矩阵
print(corr_res$p)       # p值矩阵

# 4. 画相关热图（需要安装 corrplot 包）
corrplot(corr_res$r, method = "color", type = "upper",
         addCoef.col = "black", tl.col = "black", tl.srt = 45,
         p.mat = corr_res$p, sig.level = 0.05, insig = "blank")
