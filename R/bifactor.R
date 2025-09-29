library(lavaan)
library(readr)

# 1. 读取数据
dat <- read_csv("d:/narrative3600.csv")

# 2. 定义因子和 facet 索引
factors <- list(N=1, E=2, O=3, A=4, C=5)
facet_starts <- c(0,5,10,15,20,25)
facet_offsets <- c(0,30,60,90)

# 3. 生成 facet item 列名
facet_items <- list()
for(f in names(factors)){
  facet_items[[f]] <- list()
  for(k in 1:6){
    base <- factors[[f]] + facet_starts[k]
    idxs <- base + facet_offsets
    facet_items[[f]][[k]] <- paste0("I", idxs)
  }
}

# 4. 构建 bifactor 模型语法
# 4.1 G 因子加载所有 facet items
all_items <- unlist(facet_items)
all_items_flat <- unlist(all_items)
G_line <- paste0("G =~ ", paste(all_items_flat, collapse = " + "))

# 4.2 五大因子加载各自 facet items
group_lines <- sapply(names(factors), function(f){
  items_f <- unlist(facet_items[[f]])
  paste0(f, " =~ ", paste(items_f, collapse = " + "))
})

# 4.3 因子间协方差（G 不与其他因子正交）
orth_lines <- c(
  "N ~~ E","N ~~ O","N ~~ A","N ~~ C",
  "E ~~ O","E ~~ A","E ~~ C",
  "O ~~ A","O ~~ C",
  "A ~~ C"
)

# 5. 拼接完整模型
model_bi <- paste(
  G_line,
  paste(group_lines, collapse="\n"),
  paste(orth_lines, collapse="\n"),
  sep="\n\n"
)

# 6. 拟合模型：原始 item 为 ordinal，使用 WLSMV
fit_bi <- cfa(model_bi,
              data = dat,
              estimator = "WLSMV",
              ordered = all_items_flat,
              std.lv = TRUE)
 summary(fit_bi, fit.measures = TRUE, standardized = TRUE)

# 7. 查看拟合指标
fitMeasures(fit_bi, c("cfi","tli","rmsea","srmr"))

# 8. 查看潜变量协方差，确保正定
lavInspect(fit_bi, "cov.lv")

std_loadings <- standardizedSolution(fit_bi)

# 保存为 CSV
write.csv(std_loadings, "d:/fit_bi_loadings.csv", row.names=FALSE)
