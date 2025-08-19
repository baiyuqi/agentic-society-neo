import pandas as pd

# 根据文档 Start-End 精准转换成 colspecs (0-based, end 要 +1)
def fwf_range(start, end):
    return (start - 1, end)  # pandas read_fwf 是左闭右开区间

colspecs = [
    fwf_range(1, 6),    # CASE
    fwf_range(7, 7),    # SEX
    fwf_range(8, 9),    # AGE
    fwf_range(10, 11),  # SEC
    fwf_range(12, 13),  # MIN
    fwf_range(14, 15),  # HOUR
    fwf_range(16, 17),  # DAY
    fwf_range(18, 19),  # MONTH
    fwf_range(20, 22),  # YEAR
    fwf_range(23, 31),  # COUNTRY
]

# 添加 I1 ~ I120，每列宽度1
for i in range(120):
    start = 32 + i
    end = start
    colspecs.append(fwf_range(start, end))

column_names = [
    "CASE", "SEX", "AGE", "SEC", "MIN", "HOUR", "DAY", "MONTH", "YEAR", "COUNTRY"
] + [f"I{i+1}" for i in range(120)]

# 读取
df = pd.read_fwf(
    "data/IPIP-NEO/120/IPIP120.dat",
    colspecs=colspecs,
    names=column_names,
    dtype=str,
    nrows=600  # 只读前600条
)

# 去空格
df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

# YEAR 转整数并加 1900
df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce") + 1900

# 题目转数值，0 -> NaN
item_cols = [f"I{i+1}" for i in range(120)]
df[item_cols] = df[item_cols].apply(pd.to_numeric, errors="coerce")
df[item_cols] = df[item_cols].replace(0, pd.NA)

print(df.head(2))
