# 安装并加载包
install.packages(c("psych","lavaan"))
library(psych); library(lavaan)

# 1) 获取数据（psych包自带）
data(bfi)
# 取前25题（A1..O5）
items <- bfi[, 1:25]

# 2) 反向计分
rev_keys <- c("E1","E2","O2","O5","A1","C4","C5")
max_score <- 6
items[rev_keys] <- lapply(items[rev_keys], function(x) (max_score + 1) - x)

# 3) 分包函数
parcel_mean <- function(df, cols) rowMeans(df[, cols], na.rm = TRUE)

# 每因子 3 个分包（2+2+1 分配）
A <- items[paste0("A",1:5)]
C <- items[paste0("C",1:5)]
E <- items[paste0("E",1:5)]
N <- items[paste0("N",1:5)]
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

# 4) lavaan 模型（分包 + 合理误差相关）
# 误差相关仅加在同一因子内、内容相近的分包之间（示例）
model_parcel <- '
Agreeableness =~ A_p1 + A_p2 + A_p3
Conscientiousness =~ C_p1 + C_p2 + C_p3
Extraversion =~ E_p1 + E_p2 + E_p3
Neuroticism =~ N_p1 + N_p2 + N_p3
Openness =~ O_p1 + O_p2 + O_p3

# 合理的同因子误差相关（根据内容或MI调整）
A_p1 ~~ A_p2
C_p1 ~~ C_p2
E_p1 ~~ E_p2
N_p1 ~~ N_p2
O_p1 ~~ O_p2
'

# 5) 拟合
fit_parcel <- cfa(model_parcel, data = dat, estimator = "MLR", missing = "ML")
summary(fit_parcel, fit.measures = TRUE, standardized = TRUE)
