# TERMITe 坐标体系实证验证结论（2026-08-09）

验证对象：TERMITe 流水线输出 `data/termite_parsed.csv` 的坐标字段（start/end/summit_coordinate/POT）
与 `tracks/*.bed` 的换算关系。**仅用 2 个代表性数据集**，结论对同流水线的其余 6 个数据集为推定。

## 代表性数据集（单染色体 vs 多复制子对照）

| 数据集 | 行数 | 参考基因组 | 染色体数 | 覆盖验证目标 |
|---|---|---|---|---|
| Escherichia_coli_a（TERMITe 自有, PRJNA906280） | 686 | NC_000913.3/U00096.3 | 单 | 单染色体逻辑 |
| Enterococcus_faecalis（Dar 2016, PRJEB12568） | 779 | GCF_000742975.1（NZ_CP008814.1/15/16） | **3** | 多复制子逻辑 |

## 四项证据

### 1) summit_coordinate == POT（终止点归属）
- E. coli a：686/686 一致
- E. faecalis：778/779 一致；唯一例外 `NZ_CP008816.1:1636266-1636270 -`，summit=1636268 与 POT=1636269 相差 1 nt，
  且该行 IDR=0.002、transtermhp='-'、无 U-tract 注释，属低置信边界峰，两者都在调用区间内，不影响坐标归属。

### 2) BED offset 全量换算（1-based vs 0-based 判定，决定性）
- 规则：parsed 的 `start`/`end` 为 1-based 闭区间；tracks BED 的 `chromStart`=start−1、`chromEnd`=end（0-based half-open）
- E. coli a：686/686 全部精确匹配（无 0/±1 未命中）
- E. faecalis：779/779 全部精确匹配
- 证明：parsed.csv 为 **1-based 单碱基**坐标，BED 为 0-based，**offset = −1**。单染色体与 3 条染色体处理逻辑一致。

### 3) U-tract 序列实证（序列级命中，最强证据）
- 方法：取编码链窗口 [summit−25, summit+26]，检查 TERMITe 自带注释 `transtermhp_u_tract` 字符串是否逐字命中
  （− 链先取反向互补）
- E. coli a：528/528 命中（100%，全部有 U-tract 注释的行）
- E. faecalis：662/662 命中（100%）
- 无注释行（E. coli a 158 行、E. faecalis 117 行）为无强 U-tract 的终止子，不参与比对
- 示例（E. coli a 首行）：summit=309，u_tract='tttttttTtcgacca'，
  编码链窗口= `GCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACC`，命中在 poly-T 处

### 4) T-run 富集对照
- 编码链 [summit−12, summit] 含 ≥4 个 T：
  - E. coli a：225/686（33%）vs 随机对照 4.5% → **7.3× 富集**
  - E. faecalis：423/779（54%）vs 随机对照 13.4% → **4× 富集**
- 证实 summit 落在 poly-T 富集的终止子区，非随机位置

## 结论

1. `parsed.csv` 的 start/end/summit_coordinate/POT 均为**参考基因组 1-based 单碱基坐标**；
   `tracks/*.bed` 为 0-based half-open，与 parsed 的换算为 **offset = −1**。
2. 单染色体（E. coli a）与多复制子（E. faecalis 3 条染色体，含 767/6/6 行分布）处理逻辑**完全一致**。
3. **其余 6 个数据集**（B. subtilis a–d、E. coli b、L. monocytogenes）基于同一 TERMITe 流水线代码推定，
   未逐一独立序列验证——登记时在 coordinate_convention 列已如实标注这一边界。

## 证据文件
- `draft/verify_coord_1.txt`：parsed 全列首行 / BED / GFF3 / .fai 索引
- `draft/verify_coord_2.txt`：summit==POT 与 BED offset 全量计数、U-tract 窗口初版（8nt 窗口）
- `draft/verify_coord_3.txt`：u_tract 子串逐字命中（100%）+ T-run 富集与随机对照
- `draft/verify_coord_4.txt`：唯一 summit≠POT 行的定性（低置信边界峰）
- `draft/verify_coord_5.txt`：8 个 dataset 行数与染色体分布
