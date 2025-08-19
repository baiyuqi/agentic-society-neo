import pandas as pd
from semopy import Model
import numpy as np
import semopy
# 1) 获取数据（OSF镜像）
df = pd.read_csv("https://osf.io/s87kd/download")
items = df.iloc[:, :25].copy()

# 2) 反向计分
rev = ["E1","E2","O2","O5","A1","C4","C5"]
items[rev] = 7 - items[rev]  # 1..6量表 → 反向

# 3) 分包函数
def parcel_mean(cols):
    return items[cols].mean(axis=1)

A = [f"A{i}" for i in range(1,6)]
C = [f"C{i}" for i in range(1,6)]
E = [f"E{i}" for i in range(1,6)]
N = [f"N{i}" for i in range(1,6)]
O = [f"O{i}" for i in range(1,6)]

dat = pd.DataFrame({
    "A_p1": parcel_mean([A[0],A[3]]),
    "A_p2": parcel_mean([A[1],A[4]]),
    "A_p3": items[A[2]],
    "C_p1": parcel_mean([C[0],C[3]]),
    "C_p2": parcel_mean([C[1],C[4]]),
    "C_p3": items[C[2]],
    "E_p1": parcel_mean([E[0],E[3]]),
    "E_p2": parcel_mean([E[1],E[4]]),
    "E_p3": items[E[2]],
    "N_p1": parcel_mean([N[0],N[3]]),
    "N_p2": parcel_mean([N[1],N[4]]),
    "N_p3": items[N[2]],
    "O_p1": parcel_mean([O[0],O[3]]),
    "O_p2": parcel_mean([O[1],O[4]]),
    "O_p3": items[O[2]],
})

# 4) semopy模型（分包 + 合理误差相关）
model = """
Agreeableness =~ A_p1 + A_p2 + A_p3
Conscientiousness =~ C_p1 + C_p2 + C_p3
Extraversion =~ E_p1 + E_p2 + E_p3
Neuroticism =~ N_p1 + N_p2 + N_p3
Openness =~ O_p1 + O_p2 + O_p3

A_p1 ~~ A_p2
C_p1 ~~ C_p2
E_p1 ~~ E_p2
N_p1 ~~ N_p2
O_p1 ~~ O_p2
"""

m = Model(model)
m.fit(dat)
def stat(model):
    stats = semopy.calc_stats(model)
    
    # For debugging, let's see what we got
    print("CFA Stats DataFrame:")
    print(stats)
    
    results = {}
    
    # Manually calculate p-value from chi2 and DoF for robustness
    from scipy.stats import chi2
    chi2_val = stats['chi2'].iloc[0] if 'chi2' in stats.columns else None
    dof_val = stats['DoF'].iloc[0] if 'DoF' in stats.columns else None
    
    if chi2_val is not None and dof_val is not None and dof_val > 0:
        p_value = chi2.sf(chi2_val, dof_val)
    else:
        p_value = 'N/A'

    # Mapping from our desired key to semopy's column name
    indices_to_get = {
        "chisq": "chi2",
        "df": "DoF",
        "cfi": "CFI",
        "tli": "TLI",
        "rmsea": "RMSEA",
        "gfi": "GFI"  # SRMR is often not available, GFI is a good alternative
    }

    for key, col_name in indices_to_get.items():
        if col_name in stats.columns:
            results[key] = stats[col_name].iloc[0]
        else:
            results[key] = 'N/A'
            
    results['p-value'] = p_value
    print(results)
    return results
stat(m)