# TERMITe 进展日志

## 2026-08-06 — Phase A+B 完成

### 完成工作

#### Phase A: 数据标准化
- 解析 TERMITe Supplementary Table 2（11,769 条记录，17 个数据集）
- 染色体名称映射：B. subtilis "Chromosome" → NC_000964.3，E. coli → NC_000913.3，L. monocytogenes → NC_003210.1
- 去重：176 组重复，丢弃 195 条，保留 11,574 条
- 规则：termite_score 高 → rnafold 确认(+) → 第一条
- 每个 dataset 输出 BED6+4 + GFF3 两种格式
- 输出：`data/dedup_log.csv`（含每个重复组候选记录明细）

#### Phase B: 参考基因组下载
- 从 Supplementary Table 1 提取菌株/Assembly 信息
- 使用 NCBI Datasets CLI 下载 13 个基因组（FASTA + GFF3）
- 使用 pyfaidx 生成 FASTA 索引 (.fai)
- B. subtilis (a/b/c/d) 共用 GCA_000009045，E. coli (a/b) 共用 GCA_000005845

### 环境配置
- 新建 conda 环境 `bgi`（Python 3.13 + ncbi-datasets-cli + pyfaidx）
- 项目 README 已更新，记录环境依赖

### 输出文件
```
TERMITe/
├── data/                          # Phase A 输出
│   ├── termite_parsed.csv         # 去重后完整数据
│   ├── dedup_log.csv              # 去重日志
│   └── dedup_summary.txt
├── tracks/{dataset_id}/           # Phase A 轨道文件
│   ├── {dataset_id}_terminators.bed
│   └── {dataset_id}_terminators.gff3
├── genomes/{assembly}/            # Phase B 基因组
│   ├── {assembly}.fna
│   ├── {assembly}.fna.fai
│   └── genomic.gff
├── scripts/
│   ├── parse_termit_supp_table2.py
│   ├── phaseB_download_genomes.py
│   ├── phaseC_index_tracks.py
│   └── phaseC_configure_jbrowse.py
├── jbrowse/                       # Phase C JBrowse2 实例
│   ├── index.html
│   ├── config.json                # 13 assemblies + 30 tracks
│   ├── data/                      # 所有数据文件副本
│   │   └── {assembly}/            # 每个 assembly 一个目录
│   │       ├── {assembly}.fna
│   │       ├── {assembly}.fna.fai
│   │       ├── genomic.gff
│   │       ├── {dataset}_terminators.bed
│   │       └── {assembly}.aliases.tsv (3 个物种)
│   └── aliases/                   # 染色体别名映射
│       ├── GCA_000009045.aliases.tsv
│       ├── GCA_000005845.aliases.tsv
│       └── GCA_000196035.aliases.tsv
├── gkaf553_supplemental_files/    # 原始补充材料
└── README.md
```

## 2026-08-06 — Phase C+D 完成

### Phase C: 索引与 JBrowse2 配置

#### C1: 环境安装
- ✅ `@jbrowse/cli` 已通过 npm 全局安装
- ⚠️ `htslib` (bgzip/tabix) 在 Windows 上 conda 安装超时，未安装
  - 替代方案：使用 `BedAdapter`/`Gff3Adapter`（非 tabix 版本）加载小文件
  - 细菌基因组 BED 文件较小（<1MB），无需 tabix 索引即可高效加载

#### C2: 轨道文件索引脚本
- 编写 `scripts/phaseC_index_tracks.py`（支持 bgzip/tabix CLI 和纯 Python 两种模式）
- 由于 htslib 不可用，当前使用纯 Python 模式（gzip 压缩 + 占位索引）
- 配置脚本已使用非 tabix 适配器，不依赖索引文件

#### C3: RefName Aliases 映射
- 创建 3 个染色体别名映射文件（解决 BED 轨道 NC_* 与 FASTA 中 INSDC accession 不匹配的问题）：
  - `jbrowse/aliases/GCA_000009045.aliases.tsv`：B. subtilis（AL009126.3 ↔ NC_000964.3）
  - `jbrowse/aliases/GCA_000005845.aliases.tsv`：E. coli（U00096.3 ↔ NC_000913.3）
  - `jbrowse/aliases/GCA_000196035.aliases.tsv`：L. monocytogenes（AL591824.1 ↔ NC_003210.1）

#### C4: 创建 JBrowse2 实例
- `jbrowse create jbrowse/` 完成（v4.3.0）

#### C5-C6: 配置脚本
- 编写 `scripts/phaseC_configure_jbrowse.py`，实现：
  - 自动复制基因组文件到 `jbrowse/data/{assembly}/`
  - 自动复制 BED 轨道文件到对应 assembly 目录
  - 自动添加别名映射（3 个物种）
  - 生成完整的 `config.json` 配置

#### 配置结果
| 度量 | 数量 |
|------|------|
| Assemblies | 13 |
| 基因注释轨道 | 13 |
| TERMITe 终止子轨道 | 17 |
| 轨道总数 | 30 |
| 已处理别名映射 | 3 / 3 |

### Phase D: 验证

#### D1: 本地验证
- ✅ 本地 HTTP 服务器已启动（端口 8080）
- ✅ 所有数据文件可通过 HTTP 访问：
  - 13 个 FASTA 文件 → 200 OK
  - 13 个 FAI 索引文件 → 200 OK
  - 13 个 GFF3 基因组注释文件 → 200 OK
  - 17 个 BED 轨道文件 → 200 OK
  - 3 个别名映射文件 → 200 OK
  - `config.json` → 200 OK（含 13 assemblies + 30 tracks）
- ✅ `index.html` → 200 OK
- 待验证：浏览器打开 `http://localhost:8080` 确认轨道渲染

#### D2: GitHub Pages 部署
- 待完成：将 `jbrowse/` 目录提交到 GitHub 并启用 GitHub Pages

### 关键发现与决策

#### 染色体命名不匹配
3 个物种的 TERMITe 数据使用 RefSeq accession（NC_*），而 NCBI Datasets 下载的 FASTA 使用 INSDC accession（AL_*, U_*）：
- 解决：使用 JBrowse2 的 `refNameAliases` 功能，在 assembly 配置中映射别名
- 其余 10 个物种的染色体名在轨道和 FASTA 中一致，无需处理

#### htslib 在 Windows 上不可用
- conda 安装 htslib 超时（Windows 环境）
- 解决：使用 JBrowse2 的 `BedAdapter`/`Gff3Adapter`（非 tabix 版本）
- 细菌基因组 BED 文件较小（<1MB/文件），顺序加载效率足够

### 待办
1. 浏览器打开 `http://localhost:8080` 验证轨道渲染
2. 提交 `jbrowse/` 到 GitHub 并启用 GitHub Pages
3. 后续可复用同一套 pipeline 处理 BATTER 文献 13 篇数据

---

## 2026-08-07 — 修复：BED 轨道属性字段名显示为 field6-field9

### 问题
JBrowse2 中点击终止子 feature 查看详情时，Attributes 显示无意义占位符
（field6: 1000, field7: 0.001, field8: -16.6, field9: 76.0），无法看出含义。

### 根因
- BED 文件是位置化格式，数据行本身不携带列名
- JBrowse2 的 BedAdapter 默认将标准 6 列之后的附加列命名为 field6、field7...
- 原始 Supplementary Table 2 表头核实（工作表 `Atlas of intrinsic terminators` 第2行）：
  | BED 列 | 原显示 | 原始列 | 原始列名 |
  |--------|--------|--------|---------|
  | 7 | field6 | col9 | termite score |
  | 8 | field7 | col12 | IDR |
  | 9 | field8 | col33 | rnafold energy |
  | 10 | field9 | col21 | transtermhp confidence |

### 修复方案（用户选择：仅 config 列名）
- 在 `scripts/phaseC_configure_jbrowse.py` 中为每个 BED 轨道 adapter 添加 `columnNames`
- **重要发现**：JBrowse2 的 `columnNames` 是"完整表头行"语义（`names[i]` 逐列对应
  `splitLine[i]`），必须列出**全部 10 列**名称，不能只列附加列。
  最初只填 4 个附加列名会导致错位（chrom 被标成 termite_score 等），已修正为：
  ```json
  "columnNames": ["chrom", "chromStart", "chromEnd", "name", "score", "strand",
                  "termite_score", "IDR", "rnafold_energy", "transtermhp_confidence"]
  ```
- 已用模拟 `defaultParser` 验证：10 列名映射后 Attributes 面板显示
  termite_score/IDR/rnafold_energy/transtermhp_confidence，正确
- 重新运行配置脚本，config.json 中 17 个 BED 轨道均已更新（JSON 校验通过）
- BED 文件保持纯数据行；GFF3 文件无需修改（attributes 列原本就用有意义名称）

### 数据疑点核查（POT:1744835_-）
- 该记录在 `Escherichia_coli_b`，BED 第 360 行，第 10 列 transtermhp_confidence = `.`
- 回到原始 xlsx（实际行 10487）：`transtermhp confidence` 原始值本来就是 `'.'`
- 结论：**原始表该记录本就缺失此值**，`.` 是 TERMITe 的缺失标记，解析脚本忠实保留，非 bug

### 关于 score 与 termite_score 重复
- BED 第5列 `score` 与第7列 `field6`(termite_score) 为同一数据源两次存储，**有意为之**：
  - 第5列 = termite_score 钳制到 0-1000（满足 BED 标准 score 范围）
  - 第7列 = termite_score 原始值（供明细展示）
- 本数据集评分本身在 0-1000 内，两列数值实际相同，属 BED6+4 规范做法