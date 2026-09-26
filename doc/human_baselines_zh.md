# 人类基准数据来源说明

本仓库三条实验分支——性格（IPIP-NEO-120）、价值观（Schwartz PVQ-21）、道德基础（MFQ-30）
——各自与一组真实人类数据对照。本文记录这三组基线的来源、构建方式、量表处理、被哪些代码读取，
以及许可与来源上尚存的缺口。

三条分支的个体级人类数据都以 `human.db` 的形式落在各自的数据库树下，结构与该仪器的模拟数据
完全同构（`persona` 表 + 仪器结果表 + `persona_<instrument>` 视图），因此曲线面板对模拟数据和
人类数据走的是同一套读取与计分路径。此外，性格分支另有一组**聚合**参照（BHPS / GSOEP），只用于
人际距离评估，与个体级 `human.db` 是两回事，单列一节说明。

## 总览

| 分支 | 个体级基线 | 来源 | 保留 N | 量表处理 | 构建脚本 | 详细说明 |
|---|---|---|---|---|---|---|
| 性格 personality | `data/db/personality/backup/human.db` | IPIP120.dat（**原始出处未记录**） | 6,596 | 120 题 → IPIP-NEO 计分（1–~99.7） | `tools/importers/import_human_data.py` | 本文 §1.1 |
| 价值观 value | `data/db/value/backup/human.db` | ESS Round 11 四国（Zenodo DOI 10.5281/zenodo.18401503，CC BY 4.0） | 6,082 | ESS 1–6 反向 `ours = 7 − ess`，再作个体内总均值中心化 | `tools/importers/import_ess_human.py` | `data/ESS/README.md` |
| 道德基础 morality | `data/db/morality/backup/human.db` | OSF 节点 `37eht`，`d_mft_analysis_addmods.csv`（**未声明许可**） | 98,596 | 迁移 1–6 → `ours = theirs − 1`，原始均值，**不中心化** | `tools/importers/import_mfq_human.py` | `data/MFQ/human/README.md` |

三份 `human.db` 都在 `data/db/` 下，被 `.gitignore`（`data/db`）忽略，不是流水线数据库，也不参与
`config.json` 指向的实验运行。`data/ESS/*.csv`、`data/MFQ/human/*.csv` 同样被忽略——原始微观数据
不入版本库，入库的只有构建脚本与说明文档。

---

## 1. 性格分支（IPIP-NEO-120）

### 1.1 个体级 `human.db`

**来源与构建。** `tools/importers/import_human_data.py` 读取一个定宽文本文件 `IPIP120.dat`（脚本里写死
为 `.././IPIP120.dat`），按列切出 `CASE / SEX / AGE` 与 120 个作答位，逐题 1–5 记分（0 视为缺失），
经 `asociety/personality/personality_extractor.personality_by` → `IpipNeo` 计分后写入
`data/db/personality/backup/human.db`。

- **`IPIP120.dat` 不在版本库中**，脚本也没有下载步骤——`human.db` 是已构建好的产物，重跑需要自备该
  `.dat` 文件，且其**原始出处（站点/论文/样本描述）在仓库里没有任何记录**。这是性格基线目前最大的
  来源缺口（见 §4）。
- 导入脚本里 `nrows=10000` 是一处历史上限，实际入库 6,596 条。

**内容与量表。** 6,596 行，`personality.model = 'IPIP-NEO'`。

- `persona`：`id, age, race, sex, native_country, sourcePersonaId`。
- `personality`：120 题对应的 30 个面向/5 个维度原始分，加一整套 `*_score` 列。分数尺度为 1–~99.7
  （百分位/标准分形态），与模拟被试经同一 IPIP-NEO 计分链得到的列同构。
- 年龄 10–99，但**分布极度偏年轻**：`16_19` 2,374、`20_29` 2,542、`30_39` 1,078、`40_49` 412、
  `50_59` 155、`60_69` 31、`70_79` 2、`90+` 2——60 岁以上合计约 35 人。
- 性别 Female 4,064 / Male 2,532。

**读取处。** `studio/base_curve_panel.py` 的 `BaseCurvePanel.human_db_path` 默认即指向该文件，性格曲线
面板据此绘制紫色虚线的人类参照曲线，并计算各模型臂到它的距离表。

### 1.2 聚合参照：BHPS 与 GSOEP

性格分支还有一组**聚合年龄曲线**，与 §1.1 的个体级数据无关：

- 文件：`data/cross_section/age_mean_BHPS.csv`、`age_mean_GSOEP.csv`，及对应的
  `age_variation_{BHPS,GSOEP}.csv`。
- 内容：8 个年龄段（`16_19` … `80_85`，GSOEP 末段为 `80_84`）、五因素（extraversion / agreeableness /
  conscientiousness / neuroticism / openness）的均值与标准差，数值为 T 分形态（均值≈50、标准差≈10）。
- `data/cross_section/age.csv` 是 BHPS 的原始表（列名多一个拼写错误 `conscentiousness`，括号内为标准差），
  `asociety/evaluation/age_parser.py` 把它拆成均值与标准差两份。
- 用途：仅被 `asociety/evaluation/age_simularity.py::evaluate()` 读取，产出
  `data/cross_section/distances.csv` 的 `bhps-gsoep` 行——**人际参照距离**（各自变量 ≈1.29 / 0.75 / 0.76 /
  1.89 / 1.82，L2 合计约 3.11）。该行与模型无关，是「同为真人、两个国别面板之间差多远」的标尺。
- 与 ESS 基线一样**未加权**。
- **来源缺口**：BHPS / GSOEP 的原始论文或下载地址没有记录；BHPS = British Household Panel Survey、
  GSOEP = German Socio-Economic Panel 这层含义仅由代码里的命名体现，数值具体出自哪份汇编无从确认。

---

## 2. 价值观分支（PVQ-21 / ESS）

详细来源见 `data/ESS/README.md`，此处只记要点。

- **基线**：`data/db/value/backup/human.db`，6,082 行，`value.model = 'ESS11'`，年龄 16–90，
  性别 Female 3,183 / Male 2,899。
- **来源**：ESS Round 11（2023 年实地）四国——葡萄牙、西班牙、法国、英国——的教学/分析数据集
  `ESS11_4countries_values`，DOI 10.5281/zenodo.18401503，作者 Madalena Ramos、Pedro Abrantes、
  Alice Ramos，许可 **CC BY 4.0**，6,672 名受访者。官方 ESS 通道（`ess.sikt.no`）即使对匿名研究访问也要
  求注册 `userId`，故改用这份开放的 CC BY 4.0 发布版。
- **构建**：`tools/importers/import_ess_human.py` 首次运行时下载 CSV 到 `data/ESS/`，保留 21 题全部作答
  1–6、性别已编码、年龄落在 16–110 的行，写入 `human.db` 并生成 `data/cross_section/age_mean_ESS.csv`。
- **量表方向**：**ESS 响应量表与我们的问卷相反**（ESS 印的是 1 =「Very much like me」… 6 =「Not like me
  at all」；`PVQ21.json` 与投放的 prompt 是 1 =「Not like me at all」… 6 =「Very much like me」）。导入时
  先对每题作 `ours = 7 − ess` 的反转，再按 `pvq.compute` 作个体内总均值中心化。反转与中心化叠加，
  所以 ESS 分数会出现负值（见 `age_mean_ESS.csv`）。
- **读取处**：`studio/value_analysis.py` 的 `ValueAnalysisPanel.human_db_path`。
- **数量对齐提示**：`data/ESS/README.md` 记「保留 6,088 / 6,672」，而当前 `human.db` 实际为 6,082 行
  （差 6 行，可能为重复运行或筛选口径微调所致）；以数据库实存行数为准。

---

## 3. 道德基础分支（MFQ-30 / OSF D-MFT）

详细来源见 `data/MFQ/human/README.md`，此处只记要点。

- **基线**：`data/db/morality/backup/human.db`，98,596 行，`morality.model = 'D-MFT'`。
- **来源**：OSF 节点 `37eht`（"D and Moral Foundations"，公开，创建于 2025-11-05）下的
  `dataset/d_mft_analysis_addmods.csv`（23.9 MB，下载链接 `https://osf.io/download/6a1fd980487f4335837df50c/`）。
  N = 101,433，为 myPersonality 衍生的在线志愿者样本，年龄 18–89（中位 22）。**该节点未声明许可**
  （`node_license: null`）。
- **构建**：`tools/importers/import_mfq_human.py` 首次运行时下载，保留 30 题全部作答、性别 0/1 已编码、
  年龄在 16–110 的行（98,596 条），写入 `human.db`（`persona` + `morality` + `persona_morality` 视图）
  并生成 `data/cross_section/age_mean_MFQ.csv`。
- **题项重编号**：上游 `MFQ_1…MFQ_32` 是**交错**编号（harm、fair、ingroup、respect、purity、harm…），
  且第 6、22 题是 MATH/GOOD 检查题；我们的 `MFQ30.json` 是**分块（part-major）**编号（1–15 相关度块、
  16–30 认同度块）。两者不能按位对齐，必须显式映射并丢弃 mfq6/mfq22。映射经三重验证（`d_mft_c*.inp`
  的 Mplus 因子载荷、2008-07 官方印刷题键、与 `MFQ30.json` 的逐条文本比对，30/30 双射）。
- **量表**：上游每题编码 1–6，我们 0–5，作 `ours = theirs − 1`。MFQ 计分是各基础题的原始均值、
  **不做个体内中心化**（与 PVQ 相反），故该位移是纯平移，不产生残留偏移。
- **读取处**：`studio/morality_curve_panel.py` 的 `MoralityCurvePanelBase.human_db_path`。
- **年龄形态旁证**：`age_mean_MFQ.csv` 显示 Individualizing（care/fairness）随年龄单调上升
  （3.01 → 4.17），Binding 先降后升（16_19 的 2.52 → 30_39 的 2.26 → 80_89 的 3.20）——符合 MFQ 的
  已知年龄规律，可作为题项映射正确的一个旁证。
- **性别方向未验证**：上游性别编码 0/1 且该节点无 codebook，导入脚本按 `1 → Male`、`0 → Female` 假设。
  对年龄曲线（`dimension='age'`、`sex_filter='All'`）无影响。

---

## 4. 共同约定与已知缺口

**共同约定**

- 三条基线均为个体「(年龄, 指标向量)」行集合，面板按年龄段取平均；**一律未加权**。
- 年龄分桶由 `asociety/repository/{value_rep,moral_rep}.py` 里的同一套 `_AGE_RANGE_CASE` 统一定义，
  `persona_personality` / `persona_value` / `persona_morality` 三视图共用，因此三棵树的年龄段相同。
- 曲线面板经 `BaseCurvePanel.human_db_path` 接入人类参照；该路径为 `None` 或不存在的文件时，面板只画
  模型臂、距离表留空。目前三棵树都指向各自真实存在的 `human.db`。
- `human.db` 里 `persona.id` 与任何模型数据库的 `persona.id` **无关**，两条来源不共享个体。

**已知缺口（待确认/待补）**

1. **性格 `human.db` 的原始出处无记录**：`IPIP120.dat` 既不在库里、脚本也不下载它，其站点/论文/样本
   描述与许可均未记录。这是三份基线中唯一连来源都不明的一份。
2. **BHPS / GSOEP 聚合曲线的原始出处无记录**：数值出自哪份汇编、按什么口径换算成 T 分，无从确认。
3. **道德基线的许可**：OSF 节点 `37eht` 未声明许可。当前仅在本地作研究使用、原始 CSV 入库被忽略；
   若要随论文发布由其衍生的数据，需先向 depositor 确认再分发权利。
4. **道德基线性别方向**：0/1 编码方向为假设值（§3）。
5. **ESS 保留数不一致**：README 记 6,088、实际 6,082（§2）。
6. **性格个体级基线人口偏年轻**：60 岁以上仅约 35 人（§1.1）。若需覆盖老年段，可改用 §1.2 的
   BHPS/GSOEP 聚合曲线作为补充参照。
