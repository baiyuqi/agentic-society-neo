library(lavaan)
library(readr)

# 读取数据（路径请改成你的文件路径）
file_path <- file.choose()
ipip_data <- read_csv(file_path)

# -------------------------
# IPIP-NEO-120 bifactor（G + N/E/O/A/C）自动生成模型
# - 每个条目加载在 General(G) + 对应的大维度(N/E/O/A/C)
# - G 与具体因子正交，具体因子之间正交
# -------------------------

# 五大因子起始题号（与您现有代码一致）
factors <- list(
  N = 1,  # Neuroticism
  E = 2,  # Extraversion
  O = 3,  # Openness
  A = 4,  # Agreeableness
  C = 5   # Conscientiousness
)

# 每个因子有6个facet，每facet 4题；同facet相隔30题
facet_offsets <- c(0, 30, 60, 90)       # 同一facet内的4个item
facet_starts  <- c(0, 5, 10, 15, 20, 25) # 6个facet的起点偏移

# 1) 列出每个大维度的全部条目（24题）
domain_items <- lapply(names(factors), function(f) {
  start_item <- factors[[f]]
  unlist(lapply(facet_starts, function(fs) {
    base <- start_item + fs
    base + facet_offsets
  }))
})
names(domain_items) <- names(factors)

# 2) General 因子：加载全部 120 个条目
all_items <- sort(unlist(domain_items))
G_line <- paste0("G =~ ", paste0("I", all_items, collapse = " + "))

# 3) 5 个具体因子：各自只加载各自的 24 个条目
group_lines <- sapply(names(domain_items), function(f) {
  paste0(f, " =~ ", paste0("I", domain_items[[f]], collapse = " + "))
})

# 4) 正交约束：G 与各具体因子正交；具体因子两两正交
#    lavaan 中用 "~~ 0*" 设为零相关
orthogonality_lines <- c(
  "G ~~ 0*N",
  "G ~~ 0*E",
  "G ~~ 0*O",
  "G ~~ 0*A",
  "G ~~ 0*C",
  "N ~~ 0*E",
  "N ~~ 0*O",
  "N ~~ 0*A",
  "N ~~ 0*C",
  "E ~~ 0*O",
  "E ~~ 0*A",
  "E ~~ 0*C",
  "O ~~ 0*A",
  "O ~~ 0*C",
  "A ~~ 0*C"
)

# 5) 可选：为识别性，固定各具体因子均值为0（默认即为0），方差自由；
#    使用 std.lv=TRUE 让潜变量方差=1，有助于稳定与解释。

# 6) 拼接模型语法
ipip_neo_bifactor <- paste(
  "# Bifactor 模型：General + 5 group（正交）",
  G_line,
  paste(group_lines, collapse = "\n"),
  "# 正交约束",
  paste(orthogonality_lines, collapse = "\n"),
  sep = "\n\n"
)

cat(ipip_neo_bifactor)

# ====== 拟合示例（请提前准备好 dat，列名 I1..I120；Likert 建议用 WLSMV）======
library(lavaan)
fit_bif <- cfa(
   ipip_neo_bifactor,
   data = ipip_data,
   ordered = paste0("I", 1:120),
   estimator = "WLSMV",
   std.lv = TRUE,       # 潜变量方差=1（bifactor 常用）
   missing = "pairwise"
 )
 summary(fit_bif, fit.measures = TRUE, standardized = TRUE)
 fitMeasures(fit_bif, c("cfi","tli","rmsea","srmr","chisq","df"))
 modindices <- modificationIndices(fit_bif)
 head(modindices[order(-modindices$mi), ], 20)


