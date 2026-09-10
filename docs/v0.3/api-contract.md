# BTED v0.3 API 契约

**前缀：** `/api/v1`（FastAPI alternative path）
**状态：** v0.3.0 D2：只读 FastAPI 查询层、同源资产 GET/HEAD/单 Range 代理与 assembly 级动态 JBrowse 配置已实现；该契约保留为 future/alternative。当前 Cloudflare Worker preview 使用 `/api`，详见 [`deployment.md`](deployment.md)。
**默认数据：** 当前 `published` release；所有响应显式返回 `release_version`

## 1. 通用规则

### 1.1 Release 选择

所有查询都接受 `release_version` 参数。省略时使用服务配置的 current published
release，但响应仍必须带 `release_version`、canonical manifest 路径和
`canonical_manifest_sha256`。未知版本返回 `404`，不能静默回退到另一个 release。

响应中的 `release` 摘要为：

```json
{
  "release_version": "v0.3.0",
  "status": "published",
  "canonical_manifest_sha256": "<64 lowercase hex>",
  "import_run_id": 17
}
```

`import_run_id` 只用于审计，不是 endpoint 的科学 ID。API 不允许普通请求修改 release
或 import run。

### 1.2 分页、排序与过滤

列表接口使用一致的分页参数：

- `page`：从 1 开始，默认 `1`；
- `page_size`：默认 `50`，最大 `100`；非整数、`page < 1` 或超过上限返回 `422`；
- 服务端必须给出稳定排序。默认排序为业务键升序（endpoints 为
  `end_id`，sources 为 `source_id`，assemblies 为 `assembly_accession`，genes 为
  `contig_accession, start_1based, gene_id`）；客户端可使用文档声明的 `sort` 值，
  不接受任意 SQL 表达式。

列表响应统一包含：

```json
{
  "release": {"release_version": "v0.3.0", "status": "published"},
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "returned": 0,
    "total": 0,
    "has_next": false
  }
}
```

过滤值按完整字符串匹配，除非参数名明确标为 `q`/`search`。不支持跨 contig 的模糊
坐标匹配；contig 必须通过 assembly accession + contig accession 组合确定。

### 1.3 JSON、provenance 与错误

- JSON 响应使用 `application/json; charset=utf-8`；字段使用 snake_case；未知字段不能
  让客户端失去 release/provenance 信息；
- 每个 source、endpoint、gene 和 asset 对象都返回最少一层 `provenance`，包含
  `release_version`、source/assembly 身份，以及可用时的 source manifest checksum、
  `source_table_or_file`、`original_row_reference` 或 asset SHA-256；
- `404 Not Found`：release、source、assembly、asset 或请求的资源不存在，或资源在
  该 release 不公开；
- `422 Unprocessable Entity`：分页/排序/坐标/strand/evidence/format/Range 参数
  语法正确但违反契约，例如使用 `prediction_only` 过滤公开 endpoints、负坐标、
  `bed_start` 不等于 position-1、跨 contig 组合或 `page_size=1001`；
- 错误结构固定为：

```json
{
  "error": {
    "code": "invalid_filter",
    "message": "prediction_only is not a public endpoint evidence class",
    "field": "evidence_class",
    "release_version": "v0.3.0"
  }
}
```

不要用 200 + 空数组掩盖未知 release/source/asset；已知过滤条件没有结果时才返回
200 + 空数组。

## 2. Endpoint 清单

### 2.1 `GET /api/v1/stats`

返回 release 级计数，不分页：

```json
{
  "release": {"release_version": "v0.3.0", "status": "published"},
  "sources": {
    "total": 22,
    "published_standardized": 21,
    "audit_only": 1
  },
  "endpoints": {
    "total": 28399,
    "by_evidence_class": {
      "author_called_endpoint": 24887,
      "curated_record": 3512
    }
  },
  "assemblies": {"total": 20},
  "augmentation": {"eligible_sources": 19, "scope": "source"}
}
```

计数必须按 release 和公开边界计算，不把 audit-only、预测或不可拆分混合证据计入
`endpoints.total`。示例数字只是 v0.2 的当前摘要；实现必须从导入数据计算并在 release
校验时与 manifest 对照，而不是硬编码该示例。

### 2.2 `GET /api/v1/sources`

支持参数：`release_version`、`source_id`、`species`、`assay_family`、
`release_status`、`evidence_class`、`assembly_accession`、`augmentation_eligible`（由
`used_for_batter_augmentation` 派生）、
`q`（匹配 source ID、物种、菌株、PMID、raw accession）。

每条 source 返回：

```json
{
  "source_id": "BATTER_S1_007",
  "release_status": "published_standardized",
  "species": "Streptomyces lividans TK24",
  "phylum": "Actinobacteria",
  "assay_family": "Term-seq / dRNA-seq",
  "evidence_class": "author_called_endpoint",
  "record_count": 1640,
  "augmentation_eligible": true,
  "publication": {"pmid": "31555254", "year": 2019, "doi": "10.3389/fmicb.2019.02074"},
  "assembly": {"accession": "GCF_000739105.1"},
  "accessions": [{"namespace": "ENA", "accession": "PRJEB31507", "type": "project"}],
  "links": {
    "manifest": "/api/v1/assets/<manifest-asset-id>",
    "endpoints_download": "/api/v1/downloads/endpoints?source_id=BATTER_S1_007",
    "jbrowse": "https://<site>/jbrowse/?config=<registered-config>&assembly=GCF_000739105.1"
  },
  "provenance": {
    "release_version": "v0.3.0",
    "source_manifest_sha256": "<64 lowercase hex>"
  }
}
```

`publication` 从 `publications` 关联，不从 source 重复推断 PMID/year。`audit_only` source
仍可在列表中出现用于审计，但 `links.endpoints_download`、`links.jbrowse` 必须省略或
为 `null`；S1_002 不能出现空 endpoint 下载或伪 JBrowse 入口。

### 2.3 `GET /api/v1/assemblies`

支持 `release_version`、`assembly_accession`、`species`、`contig_accession`、
`q`。返回带版本的 assembly accession、物种/名称、contig 列表、来源数、公开端点数
和 release/provenance。一个 assembly 可以有多个独立 source track；统计不把不同来源
的相同坐标自动去重。

```json
{
  "assembly_accession": "GCF_000739105.1",
  "contigs": [
    {"accession": "CP009124.1", "name": "CP009124.1", "length_bp": 8283950}
  ],
  "source_count": 2,
  "gene_count": 4123,
  "endpoint_count": 2848,
  "provenance": {"release_version": "v0.3.0"}
}
```

### 2.4 `GET /api/v1/endpoints`

支持参数：`release_version`、`source_id`、`assembly_accession`、`contig_accession`、
`sample_id`、`strand`（`+`/`-`）、`evidence_class`（仅四个公开层）、
`author_category`、`gene_or_locus`、`position_min`、`position_max`、`q`（稳定 ID/作者
ID/原始行引用），以及通用 `page`/`page_size`。

响应的每个 `data` 元素必须包含 v0.2 24 列的原名和值，不能用嵌套对象替换这些列：

```json
{
  "end_id": "BTED_BATTER_S1_007_...",
  "source_id": "BATTER_S1_007",
  "sample_id": "LEE2019_TERMSEQ_PUBLISHED_TEP",
  "assay": "Term-seq",
  "evidence_class": "author_called_endpoint",
  "author_endpoint_id": "BATTER_S1_007_LEE2019_TERMSEQ_CP009124_1_R_000001",
  "published_reference_accession": "CP009124.1",
  "reference_assembly": "GCF_000739105.1",
  "reference_name": "CP009124.1",
  "replicon_label": "CP009124.1",
  "biological_coordinate_1based": 67368,
  "bed_start_0based": 67367,
  "bed_end_0based": 67368,
  "strand": "-",
  "signal_or_score": "-1.372769946",
  "author_category": "P",
  "associated_gene_or_locus": "SLIV_00320",
  "pmid": "31555254",
  "doi": "10.3389/fmicb.2019.02074",
  "source_table_or_file": "Supplementary Dataset 3 / Table_6.XLSX",
  "coordinate_interpretation": "author genomic Position treated as 1-based; BED start=Position-1",
  "original_row_reference": "...:row=2",
  "qc_status": "migrated_coordinate_and_bed_checked",
  "note": "Author-called transcript 3′ end position (TEP); this is not a per-site terminator-function claim.",
  "provenance": {
    "release_version": "v0.3.0",
    "source_manifest_sha256": "<64 lowercase hex>",
    "contig_accession": "CP009124.1"
  }
}
```

`signal_or_score` 可为 `NA`，不能为了排序改变成 null 或 0。默认不返回预测注释；如
未来增加显式 `include_annotations=true`，返回的预测字段必须标记
`annotation_kind=prediction_annotation`，且不能改变 endpoint 的 evidence class。

### 2.5 `GET /api/v1/genes`

支持 `release_version`、`assembly_accession`、`contig_accession`、`gene_id`、
`locus_tag`、`feature_type`、`start_min`、`start_max`，并提供普通分页/排序。返回 genes
的 1-based 区间、strand、assembly/contig 和 provenance。assembly list/detail 同时返回
同一 release 的 `gene_count`，作为 GFF-derived query layer 的记录数。第一版不返回 gene
clusters、Rfam 命中或推测的终止功能；`endpoint_gene_context` 尚未计算时不能伪造
`nearest_gene`。

### 2.6 `GET /api/v1/augmentation`

这是**来源级** augmentation 登记接口。参数只有 `release_version`，可用普通分页；
第一版固定筛选 `sources.used_for_batter_augmentation = TRUE`（API alias 为
`augmentation_eligible`），不支持把 endpoint ID、预测
分数、gene cluster、Rfam 或训练 split 作为查询条件。

响应必须明确范围：

```json
{
  "release": {"release_version": "v0.3.0", "status": "published"},
  "scope": "source",
  "selection_rule": "BATTER Table S1 used_for_batter_augmentation = TRUE",
  "eligible_source_count": 19,
  "training_claim": "none; source-level eligibility only",
  "data": [
    {
      "source_id": "BATTER_S1_007",
      "record_count": 1640,
      "evidence_class": "author_called_endpoint",
      "publication": {"pmid": "31555254", "year": 2019},
      "assembly_accession": "GCF_000739105.1",
      "provenance": {"release_version": "v0.3.0"}
    }
  ],
  "pagination": {"page": 1, "page_size": 50, "returned": 19, "total": 19, "has_next": false}
}
```

当前 22 个 source 中 19 个 TRUE、3 个 FALSE（S1_002、S1_021、S1_022）。API 可以在
未来增加审计统计，但不能把该接口文案写成“19 个来源的每条端点已进入训练”。

### 2.7 `GET /api/v1/downloads/endpoints`

按 release 和过滤条件流式下载 canonical endpoint 视图。支持：

- `release_version`（默认 current published）；
- `source_id`（可重复参数，要求同一 release）；
- `assembly_accession`、`contig_accession`、`gene_or_locus`、`evidence_class`、`strand`、
  `position_min`、`position_max`；这些过滤沿用 endpoint 查询层的 1-based 坐标语义；
- `format=tsv`（默认，含 24 列）或 `format=bed6`（1-based→0-based 单碱 BED6）；
- `include_annotations=false|true`：仅在许可允许且显式为 true 时附加
  `source_annotations`，预测字段必须带 `prediction_annotation` 属性。

未知 source/assembly 返回 `404`；非法 format、跨 assembly/contig 组合、预测/混合
证据过滤或不允许的 annotation 组合返回 `422`。有合法过滤但结果为零时返回 200 的
空文件和 header，而不是构造占位行。

成功响应至少包含：

```text
200 OK
Content-Type: text/tab-separated-values; charset=utf-8
Content-Disposition: attachment; filename="BTED-v0.3.0-endpoints.tsv"
X-BTED-Release-Version: v0.3.0
X-BTED-Manifest-SHA256: <64 lowercase hex>
```

`bed6` 必须输出 `chrom`, `start`, `end`, `name`, `score`, `strand`，其中 `start =
biological_coordinate_1based - 1`、`end = biological_coordinate_1based`；不能跨 contig
拼接为一个不带 assembly/contig 语义的文件。下载链接只能由 published source 生成，
S1_002 没有下载入口。

### 2.8 `GET|HEAD /api/v1/assets/{asset_id}`

同源资产入口只接受 `assets` 表中已登记、公开且 checksum/byte size 可验证的
`asset_id`。它是 Vercel/浏览器可用的稳定 URL，服务端再访问允许的 Hugging Face
origin；请求不能携带任意 `url` 查询参数。

#### 不带 Range

```text
GET /api/v1/assets/v0.3.0-assembly-gcf000739105-fasta
200 OK
Accept-Ranges: bytes
Content-Length: <asset.byte_size>
Content-Type: application/octet-stream
ETag: "sha256:<asset.sha256>"
X-BTED-Release-Version: v0.3.0
```

`HEAD` 返回相同 headers、无 body。`404` 表示 asset ID 不存在、所属 release 未发布、
或资产不可公开；不能把错误对象地址透传给浏览器。

#### 单 Range 请求

只承诺单个闭合/半闭合等价的 `bytes=start-end` 请求。满足范围时：

```text
GET /api/v1/assets/<asset_id>
Range: bytes=0-127

206 Partial Content
Accept-Ranges: bytes
Content-Range: bytes 0-127/<asset.byte_size>
Content-Length: 128
ETag: "sha256:<asset.sha256>"
X-BTED-Release-Version: v0.3.0
```

`Content-Range` 的起止值为 0-based inclusive，`Content-Length = end - start + 1`；
完整 SHA-256 只在资产登记/导入阶段由 importer 从 canonical/object 文件复算并写入
`assets.sha256`；每次 partial request 不重算整文件 checksum。请求处理只需校验资产
allowlist/公开状态、登记的 `byte_size`、origin 返回的 `Content-Range` 与返回 body
长度，并用登记的 SHA-256 生成 ETag。未满足
`0 <= start <= end < byte_size` 返回 `416 Range Not Satisfiable` 并给出
`Content-Range: bytes */<asset.byte_size>`。多段 Range 在第一版返回 416，不返回未定义
的 multipart 结果。资产不支持 Range 时返回 `416` 或明确的 `422`，不能假装 206。

### 2.9 详情接口

详情路由与列表路由使用同一 `release_version` 选择和 provenance 规则。路径 ID 是
响应中返回的稳定业务 ID；详情请求不因当前 release 没有该 ID 而回退到另一个版本。
四个详情响应都返回 `release`、`provenance` 和资源的 `links`；未知 ID 或该版本中不
公开的资源返回 `404`。

#### `GET /api/v1/sources/{source_id}`

返回单个 source 的完整详情，至少包括 species/phylum/assay/evidence/status、
`record_count`、`used_for_batter_augmentation`（API JSON 中可同时提供只读别名
`augmentation_eligible`）、publication、assembly、raw accession 和链接：

```json
{
  "release": {"release_version": "v0.3.0", "status": "published"},
  "source_id": "BATTER_S1_007",
  "publication": {
    "pmid": "31555254",
    "year": 2019,
    "doi": "10.3389/fmicb.2019.02074",
    "links": {
      "pubmed": "https://pubmed.ncbi.nlm.nih.gov/31555254/",
      "doi": "https://doi.org/10.3389/fmicb.2019.02074",
      "pmc": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6742748/"
    }
  },
  "raw_accessions": [
    {"namespace": "ENA", "accession": "PRJEB31507", "type": "project",
     "url": "https://www.ebi.ac.uk/ena/browser/view/PRJEB31507"}
  ],
  "links": {
    "bted_record": "/sources/BATTER_S1_007",
    "endpoints_download": "/api/v1/downloads/endpoints?source_id=BATTER_S1_007",
    "jbrowse": "https://<site>/jbrowse/?config=<registered-config>&assembly=GCF_000739105.1"
  },
  "provenance": {
    "release_version": "v0.3.0",
    "source_manifest_sha256": "<64 lowercase hex>"
  }
}
```

`BATTER_S1_002` 详情仍可返回其 publication、raw accession、manifest 和 audit note，
但必须明确 `release_status = audit_only`、`record_count = 0`，并省略或置空
`links.endpoints_download`、`links.jbrowse`；不得生成空 endpoint 详情或浏览器入口。

#### `GET /api/v1/assemblies/{assembly_id}`

返回 assembly 详情：带版本的 accession、strain/organism、contigs、该 release 的
独立 source tracks、gene_count、端点计数、已登记参考/GFF3 asset 及 provenance。`assembly_id` 是
数据库返回的稳定资源 ID；响应同时给出 `assembly_accession`，不能用不带版本的名称
代替。每个 source track 都链接到 `/api/v1/sources/{source_id}`，相同 assembly 的
不同研究不能合并为一个 source。

#### `GET /api/v1/endpoints/{end_id}`

返回一个 endpoint 的全部 24 列，不允许详情接口减少为坐标和分值。额外返回 source、
sample、contig、24 列中可得的 publication PMID/DOI、raw accession links、可用的
`source_annotations` 摘要和 `provenance`（包括 source manifest、`source_table_or_file`、
`original_row_reference`、release）。endpoint 的 JBrowse link 只能来自其 published
source/registered asset；S1_002 没有 endpoint ID，因此请求该 ID 返回 `404`。
完整的 publication title/journal/year 等信息通过 source detail 的 publication 关联查看，
不在 endpoint 24 列接口中重复拼接。

#### `GET /api/v1/genes/{gene_id}`

返回 gene 的 release、assembly、contig、1-based 区间、strand、gene/locus label、
annotation asset ID 与 SHA-256 provenance，并可给出同一 release 的已计算
`endpoint_gene_context`。尚未计算的 context 不返回伪造的 nearest gene；gene clusters
和 Rfam 不是该接口字段。跨 release 同名 gene 必须通过 `release_version` 选择，不能
混用不同 GFF3 annotation。

## 3. JBrowse deep link

JBrowse 链接属于 source/assembly 的 provenance，不是客户端拼接的任意路径。source 只有在
`release_status = published_standardized`、`record_count > 0` 且存在公开 endpoint BED
asset 时才返回 `has_jbrowse = TRUE` 和 `links.jbrowse`；旧的 `has_jbrowse` 标志本身不
足以生成入口。assembly 还必须有公开 FASTA+FAI，且至少有一个满足上述条件的 source，
并使用已登记 config/FASTA/FAI/GFF/BED asset ID。链接可附带 `assembly`、`loc`、`tracks` 参数，默认
窗口必须在同一 assembly/contig 中；不得跨 contig 生成 loc。

`S1_002` 的 `links.jbrowse` 必须缺失或为 null；不能因为该 source 有参考组装就生成
浏览器入口。`external_link_only` 的 raw accession/repository 链接仍可保留，但私有
asset 不得通过 asset proxy 或 JBrowse config 暴露。预测轨道和不可拆分混合证据不能
出现在该链接引用的公开配置中。

## 4. 与 canonical release 的关系

API 返回的是 release 的可查询投影。下载内容和资产对象必须能够回到 canonical
manifest、source manifest、`source_table_or_file`/`original_row_reference` 和
checksum。API 不能在运行时重新解释作者坐标、合并同坐标 endpoint 或从模型预测补齐
缺失数据；任何科学数据变化都要先生成新 release 并重新导入。

v0.3.0 D2 已实现不写库的 FastAPI 读层、登记资产的 GET/HEAD/单 Range 代理和 assembly
级动态 JBrowse 配置，但仍不实现 Hugging Face 上传、gene context 计算或训练集生成。本文件冻结路径、字段、边界、
错误和 Range 行为；当前实现不连接真实 PostgreSQL 或远端 smoke test，后续实现必须保持这些
合约。

## 5. C1/C2 只读实现说明

实现位于 `backend/app/`：`ReadService` 独立承载 release、分页、排序、证据边界和
S1_002 规则，`PostgresReadRepository` 负责参数化 PostgreSQL 查询，`create_app()` 提供
可注入 repository 的 FastAPI app factory。默认 release 是数据库中
`is_current = true AND status = 'published'` 的版本；显式传入未知 release 返回 404，
不会回退到其它版本。每个 repository 操作独立打开并关闭连接；排序字段使用固定白名单，
请求值不会拼接为 SQL。

当前可用路由为 health、stats、sources、assemblies、endpoints、genes、augmentation，
`downloads/endpoints` 的流式 TSV/BED6 导出，`GET|HEAD /api/v1/assets/{asset_id}`，以及
`GET /api/v1/assemblies/{assembly_id}/jbrowse-config`。最后一个接口从同一 release 的
assembly/source/assets 查询结果按请求生成 JBrowse JSON：FASTA+FAI 是必要参考资产；
GFF3+TBI 存在时生成共享基因注释轨道；每个 published source 的 BED 保持独立 endpoint
track，且只有公开 BED source 才被纳入配置。已登记 BigWig 才生成 observed-signal track；双链 BigWig 以
`MultiQuantitativeTrack` 紧凑展示，保留正值原始数值并标明 `normalization=none`、
`display_transform=none`。轨道 metadata 包含 PMID/DOI、raw accession URL 和
release/source provenance；S1_002 不进入配置。
endpoint 响应保留 v0.2 的全部 24 列；
BED6 的 `score` 暂固定为 `0`，原始 `signal_or_score` 只在 TSV/JSON 中保留，不把显示字段
冒充实验信号。`include_annotations=true` 在 C1 明确返回 422，待许可和附表导出边界
单独实现。C2 的资产代理只查询当前 published release 中 `is_public=true` 的登记行；
origin 必须是登记的 HTTPS URL 且 hostname 与 `origin_host` 一致，路由不接受 `url` 查询
参数。无 Range 的 GET/HEAD 返回登记的 Content-Length、Content-Type、ETag 和 release
header；单个 `bytes=start-end`、`start-` 或 `-suffix` 通过上游 Range 返回 206，非法、
多段或不支持 Range 返回 416 和 `Content-Range: bytes */size`。C2 不实现多 Range、缓存、
重试、整文件运行时 hash、HF 上传或真实网络 smoke test。endpoint 详情保留 24 列中的
PMID/DOI，并返回 source-annotation 行数/证据类别摘要；完整 publication 信息从 source
detail 获取。如果 fake repository 未提供该摘要，响应会明确标为 `not_loaded_in_c1`，而
不是伪造附表内容。published source 的 JBrowse 链接现在通过同源
`/api/v1/assemblies/{assembly_id}/jbrowse-config?source_id={source_id}` 作为 URL-encoded
`config` 参数生成；audit-only source 仍无 endpoint/JBrowse 入口。

FastAPI、uvicorn、httpx 和 psycopg3 是可选运行依赖，统一列在根目录
`requirements-v03.txt`；本仓库的离线测试不安装依赖，也不连接真实数据库。当前测试覆盖
纯 Python service/repository contract；C2 的 asset proxy 测试使用 `httpx.MockTransport`。
若环境缺少 FastAPI，runtime smoke test 会被明确标记为 skipped，而不是报告为通过。安装
依赖后可用 `backend.app.main.create_app()` 注入 fake repository/client 做 HTTP contract smoke
test，再配置显式 `BTED_DATABASE_URL` 执行隔离环境的只读查询。
