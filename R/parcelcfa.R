# 安装依赖
install.packages(c("psych","lavaan"))
library(psych); library(lavaan)

# 1) 取数据（任选其一）
data(bfi)  # 直接用内置数据
# 或者读 OSF 镜像 CSV：
# bfi <- read.csv("https://osf.io/s87kd/download", stringsAsFactors = FALSE)

# 2) 只取前25道题（A1..O5），并做反向计分（见教程与文档）
items <- bfi[, 1:25]
rev_keys <- c("E1","E2","O2","O5","A1","C4","C5")  # 常见反向题集合
max_score <- 6
items[rev_keys] <- lapply(items[rev_keys], function(x) (max_score + 1) - x)  # 反向到正向

# 3) 为每个因子做3个分包（示例：平衡分配 2+2+1）
parcel_mean <- function(df, cols) rowMeans(df[, cols], na.rm = TRUE)

A <- items[paste0("A",1:5)]; C <- items[paste0("C",1:5)]
E <- items[paste0("E",1:5)]; N <- items[paste0("N",1:5)]
O <- items[paste0("O",1:5)]

dat <- data.frame(
  A_p1 = parcel_mean(A, c(1,4)),
  A_p2 = parcel_mean(A, c(2,5)),
  A_p3 = A[,3],

  C_p1 = parcel_mean(C, c(1,4)),
  C_p2 = parcel_mean(C, c(2,5)),
  C_p3 = C[,3],

  E_p1 = parcel_mean(E, c(1,4)),
  E_p2 = parcel_mean(E, c(2,5)),
  E_p3 = E[,3],

  N_p1 = parcel_mean(N, c(1,4)),
  N_p2 = parcel_mean(N, c(2,5)),
  N_p3 = N[,3],

  O_p1 = parcel_mean(O, c(1,4)),
  O_p2 = parcel_mean(O, c(2,5)),
  O_p3 = O[,3]
)

# 4) 5因子分包CFA模型（因子相关）
model_parcel <- '
Agreeableness =~ A_p1 + A_p2 + A_p3
Conscientiousness =~ C_p1 + C_p2 + C_p3
Extraversion =~ E_p1 + E_p2 + E_p3
Neuroticism =~ N_p1 + N_p2 + N_p3
Openness =~ O_p1 + O_p2 + O_p3
'

fit_parcel <- cfa(model_parcel, data = dat, estimator = "MLR", missing = "ML")
summary(fit_parcel, fit.measures = TRUE, standardized = TRUE)
