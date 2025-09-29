library(lavaan)
library(readr)

# 2. 读取数据
dat <- read_csv("d:/human-600-2.csv")

# 1) 定义因子和 facet
factors <- list(N=1,E=2,O=3,A=4,C=5)
facet_offsets <- c(0,30,60,90)
facet_starts  <- c(0,5,10,15,20,25)

# 2) 生成 30 个 facet 变量（均值）
for(f in names(factors)){
  for(k in 1:6){
    base <- factors[[f]] + facet_starts[k]
    idxs <- base + facet_offsets
    vname <- paste0(f, k)   # e.g., N1..N6, E1..E6
    dat[[vname]] <- rowMeans(dat[paste0("I", idxs)], na.rm=TRUE)
  }
}
facet_names <- paste0(rep(names(factors), each=6), 1:6)  # N1..N6,E1..E6,...

# 3) 构建 facet-level bifactor 模型语法
G_line <- paste0("G =~ ", paste(facet_names, collapse = " + "))
group_lines <- sapply(names(factors), function(f) {
  paste0(f, " =~ ", paste0(f, 1:6, collapse = " + "))
})

# 4) 因子间协方差（G 不强制正交）
orth_lines <- c(
  "N ~~ E","N ~~ O","N ~~ A","N ~~ C",
  "E ~~ O","E ~~ A","E ~~ C",
  "O ~~ A","O ~~ C",
  "A ~~ C"
)

# 5) 残差相关：facet 内部 4 个 item 两两相关
resid_lines <- unlist(lapply(names(factors), function(f) {
  sapply(1:6, function(k) {
    # facet 内 4 个原始 item 编号
    base <- factors[[f]] + facet_starts[k]
    items <- paste0("I", base + facet_offsets)
    comb <- combn(items, 2)
    apply(comb, 2, function(x) sprintf("%s ~~ %s", x[1], x[2]))
  })
}))

# 6) 拼接完整模型
model_bi_resid <- paste(
  G_line,
  paste(group_lines, collapse="\n"),
  paste(orth_lines, collapse="\n"),
  #paste(resid_lines, collapse="\n"),
  sep="\n\n"
)

# 7) 拟合模型（facet-level 已近似连续，可用 MLR 或 WLSMV）
fit_facet <- cfa(model_bi_resid, data=dat, estimator="WLSMV", std.lv=TRUE, se="none")
 summary(fit_facet, fit.measures = TRUE, standardized = TRUE)
# 8) 查看拟合指标
fitMeasures(fit_facet, c("cfi","tli","rmsea","srmr"))
