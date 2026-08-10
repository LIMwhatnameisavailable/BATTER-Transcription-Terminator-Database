#!/usr/bin/env python3
"""Build a portable BTED release from the local BGIRNA working snapshot.

This is a one-time migration tool, deliberately kept in the repository so that
the provenance of the first BTED release remains inspectable.  It does *not*
copy raw sequencing files, publisher workbooks, FASTA/GFF files or browser
assets.  Instead it:

* normalizes eligible local result tables to the 24-column BTED schema;
* writes a BED companion only for public experimental endpoint records;
* copies the 22 source manifests and human-readable processing records;
* records excluded mixed-evidence / prediction-only assets by checksum and
  location, without placing those records in ``data/public``.

The input root must be the local BGIRNA working tree.  It is intentionally an
explicit command-line argument: no personal absolute path is stored in output
files and a future curator can rerun the migration from another machine.

Usage:
    python3 scripts/build_local_snapshot_release.py \
      --input-root /path/to/BGIRNA
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_DATE = "2026-08-10"

ENDPOINT_COLUMNS = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession",
    "reference_assembly", "reference_name", "replicon_label",
    "biological_coordinate_1based", "bed_start_0based", "bed_end_0based",
    "strand", "signal_or_score", "author_category",
    "associated_gene_or_locus", "pmid", "doi", "source_table_or_file",
    "coordinate_interpretation", "original_row_reference", "qc_status", "note",
]

PUBLIC_EVIDENCE = {
    "observed_signal",
    "called_endpoint",
    "author_called_endpoint",
    "curated_record",
}


# The four Lalanne records are literature-curated records, rather than a new
# endpoint call from the local Rend-seq signal.  Therefore they are released as
# metadata TSVs only (no public BED/browser claim).  All other listed tables
# are author-published experimental 3′ end tables.
PUBLIC_TABLES = {
    "BATTER_S1_001": {
        "input": "data/batter_ecoli_pilot/processed/literature_curated_terminator_records.ecoli.tsv",
        "asset": "curated_records.tsv",
        "evidence": "curated_record",
        "sample": "CURATED_LALANNE_TABLE_S3",
        "assay": "Rend-seq / literature curation",
        "note": "Literature-curated experimental/sequence-supported intrinsic-terminator record; not a new local terminator call.",
    },
    "BATTER_S1_003": {
        "input": "data/batter_bsub_pilot/processed/literature_curated_terminator_records.bsub.tsv",
        "asset": "curated_records.tsv",
        "evidence": "curated_record",
        "sample": "CURATED_LALANNE_TABLE_S3",
        "assay": "Rend-seq / literature curation",
        "note": "Literature-curated experimental/sequence-supported intrinsic-terminator record; local candidate peaks remain a separate signal layer.",
    },
    "BATTER_S1_004": {
        "input": "data/batter_ccre_pilot/processed/literature_curated_terminator_records.ccre.tsv",
        "asset": "curated_records.tsv",
        "evidence": "curated_record",
        "sample": "CURATED_LALANNE_TABLE_S3",
        "assay": "Rend-seq / literature curation",
        "note": "Literature-curated record; the retained GEO metadata conflict is documented in the source processing record.",
    },
    "BATTER_S1_005": {
        "input": "data/batter_vnat_pilot/processed/literature_curated_terminator_records.vnat.tsv",
        "asset": "curated_records.tsv",
        "evidence": "curated_record",
        "sample": "CURATED_LALANNE_TABLE_S3",
        "assay": "Rend-seq / literature curation",
        "note": "Literature-curated record on the two-contig reference; manual review status remains documented in the source manifest.",
    },
    "BATTER_S1_006": {
        "input": "data/spneumoniae/processed/BATTER_S1_006/published_termseq_tts.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "POOLED_TERMSEQ",
        "assay": "Term-seq",
        "note": "Author-called Term-seq TTS; author threshold and locus relationships are retained in the processing record.",
    },
    "BATTER_S1_007": {
        "input": "data/sliv2019_lee/processed/BATTER_S1_007/published_termseq_teps.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "AUTHOR_PUBLISHED",
        "assay": "Term-seq",
        "note": "Author-called transcript 3′ end position (TEP); this is not a per-site terminator-function claim.",
    },
    "BATTER_S1_008": {
        "input": "data/paeruginosa/processed/BATTER_S1_008/reproducible_termseq_3prime_sites.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "REPRODUCIBLE_TERMSEQ",
        "assay": "Term-seq",
        "note": "Author-reported reproducible Term-seq 3′ sites (Table S1B); the separate gene-associated table is documented but not duplicated here.",
    },
    "BATTER_S1_009": {
        "input": "data/zmobilis/processed/BATTER_S1_009/processing_filtered_termseq_tts.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "AUTHOR_FILTERED_TERMSEQ",
        "assay": "Term-seq",
        "note": "Author-published Term-seq TTS after processing-site filtering; pure TransTermHP predictions are excluded.",
    },
    "BATTER_S1_010": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_010/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint."},
    "BATTER_S1_011": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_011/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint."},
    "BATTER_S1_012": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_012/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint."},
    "BATTER_S1_013": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_013/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint; independent from BATTER_S1_007 despite shared organism/reference."},
    "BATTER_S1_014": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_014/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint."},
    "BATTER_S1_015": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_015/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint; chromosome and plasmid are retained as separate contigs."},
    "BATTER_S1_016": {"input": "data/streptomyces_lee2020/processed/BATTER_S1_016/published_termseq_endpoints.tsv", "asset": "endpoints.tsv", "evidence": "author_called_endpoint", "sample": "AUTHOR_PUBLISHED", "assay": "Term-seq", "note": "Author-published Term-seq endpoint; taxonomy label conflict is retained in the source record."},
    "BATTER_S1_017": {
        "input": "data/scla2021_hwang/processed/BATTER_S1_017/published_termseq_teps.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "AUTHOR_PUBLISHED",
        "assay": "Term-seq",
        "note": "Author-called Term-seq TEP; independent from BATTER_S1_015 despite shared strain/reference.",
    },
    "BATTER_S1_018": {
        "input": "data/synechocystis/processed/BATTER_S1_018/published_termseq_teps.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "AUTHOR_PUBLISHED",
        "assay": "Term-seq",
        "note": "Author-called Term-seq TEP; all four published replicons are preserved.",
    },
    "BATTER_S1_019": {
        "input": "data/synechocystis/processed/BATTER_S1_019/published_termseq_teps.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "AUTHOR_PUBLISHED",
        "assay": "Term-seq",
        "note": "Author-called manually curated Term-seq TEP.",
    },
    "BATTER_S1_020": {
        "input": "data/dickeya/processed/BATTER_S1_020/nanopore_native_rna_3prime_ends.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "NANOPORE_NATIVE_RNA",
        "assay": "Nanopore native RNA-seq",
        "note": "Author-called Nanopore native RNA 3′ end. The mixed-evidence S1C table is excluded from this public asset.",
    },
    "BATTER_S1_021": {
        "input": "data/bburgdorferi/processed/BATTER_S1_021/unique_3prime_end_sites.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "LOG_AND_TRANSITION_STATIONARY",
        "assay": "3′ RNA-seq",
        "note": "Unique author-reported 3′ RNA-seq sites. Condition-level observations are intentionally not duplicated in the public endpoint table.",
    },
    "BATTER_S1_022": {
        "input": "data/mtuberculosis/processed/BATTER_S1_022/author_classified_termseq_tts.tsv",
        "asset": "endpoints.tsv",
        "evidence": "author_called_endpoint",
        "sample": "AUTHOR_PUBLISHED",
        "assay": "Term-seq",
        "note": "Author-called Term-seq TTS. Prediction-support columns are retained only as author annotations; prediction-only RUT records are excluded.",
    },
}

AUDIT_ONLY = {
    "BATTER_S1_002": [
        {
            "local_path": "data/trs_ecoli_2023/processed/BATTER_S1_002/author_integrated_trs_3prime_termini.tsv",
            "evidence_class": "author_integrated_mixed_evidence",
            "reason": "Author Supplementary Data 3 combines RNAtag-seq and Term-seq/TRS summary evidence. It is retained as a checksum-addressable local audit asset, not a public endpoint table.",
        },
        {
            "local_path": "data/trs_ecoli_2023/processed/BATTER_S1_002/dataset_level_trs_3prime_observations.tsv",
            "evidence_class": "observed_signal",
            "reason": "Dataset-level observations need their original per-dataset provenance fields reconciled to the public endpoint schema before release; no endpoint table is emitted in this migration.",
        },
    ],
    "BATTER_S1_020": [
        {
            "local_path": "data/dickeya/processed/BATTER_S1_020/author_integrated_tts.tsv",
            "evidence_class": "author_integrated_mixed_evidence",
            "reason": "Supplementary Table S1C integrates experimental and prediction evidence; excluded from public endpoint data by BTED policy.",
        },
    ],
    "BATTER_S1_022": [
        {
            "local_path": "data/mtuberculosis/processed/BATTER_S1_022/rhotermpredict_rut_sites.prediction_only.tsv",
            "evidence_class": "prediction_only",
            "reason": "Pure RhoTermPredict RUT sites; not experimental endpoint data and not mirrored in this public repository.",
        },
    ],
}

PROCESSING_RECORDS = {
    "BATTER_S1_001": "docs/BATTER_S1_001_Ecoli_RendSeq_标准化处理记录.md",
    "BATTER_S1_002": "docs/BATTER_S1_002_Ecoli_TRS_标准化处理记录.md",
    "BATTER_S1_003": "docs/BATTER_S1_003_Bsub_RendSeq_标准化处理记录.md",
    "BATTER_S1_004": "docs/BATTER_S1_004_Ccre_RendSeq_标准化处理记录.md",
    "BATTER_S1_006": "docs/BATTER_S1_006_Spneumoniae_TermSeq_标准化处理记录.md",
    "BATTER_S1_007": "docs/BATTER_S1_007_Sliv2019_TermSeq_标准化处理记录.md",
    "BATTER_S1_008": "docs/BATTER_S1_008_PAO1_TermSeq_标准化处理记录.md",
    "BATTER_S1_009": "docs/BATTER_S1_009_Zmobilis_TermSeq_标准化处理记录.md",
    "BATTER_S1_017": "docs/BATTER_S1_017_Scla2021_TermSeq_标准化处理记录.md",
    "BATTER_S1_020": "docs/BATTER_S1_020_Dickeya_Nanopore_标准化处理记录.md",
    "BATTER_S1_021": "docs/BATTER_S1_021_Bburgdorferi_3RNASeq_标准化处理记录.md",
}
for source_num in range(10, 17):
    PROCESSING_RECORDS[f"BATTER_S1_{source_num:03d}"] = "docs/BATTER_S1_010-016_Lee2020_TermSeq_标准化处理记录.md"
for source_num in (18, 19):
    PROCESSING_RECORDS[f"BATTER_S1_{source_num:03d}"] = "docs/BATTER_S1_018-019_Synechocystis_TermSeq_标准化处理记录.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean(value: str | None, fallback: str = "NA") -> str:
    value = (value or "").strip()
    return value if value else fallback


def first_value(row: dict[str, str], names: Iterable[str], fallback: str = "NA") -> str:
    for name in names:
        value = clean(row.get(name), "")
        if value and value.upper() != "NA":
            return value
    return fallback


def id_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_]+", "-", value.strip()).strip("-")
    return token or "NA"


def read_registry() -> dict[str, dict[str, str]]:
    path = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["source_id"]: row for row in csv.DictReader(handle, delimiter="\t")}


def canonical_row(
    source_id: str,
    row: dict[str, str],
    row_number: int,
    config: dict[str, str],
    registry_row: dict[str, str],
    source_input_rel: str,
) -> dict[str, str]:
    sample = first_value(row, ["sample_id"], config["sample"])
    assay = first_value(row, ["assay"], config["assay"])
    reference_name = first_value(row, ["reference_name", "chrom", "published_replicon", "published_sequence_label", "chromosome_label"])
    replicon = first_value(row, ["replicon_label", "published_replicon", "published_sequence_label", "chromosome_label"], reference_name)
    position = first_value(row, ["biological_coordinate_1based", "published_coordinate_1based"])
    strand = first_value(row, ["strand"])
    author_id = first_value(
        row,
        ["author_endpoint_id", "author_tts_id", "author_tep_id", "genomic_site_id", "literature_end_id", "site_id", "end_id", "record_id"],
        f"row_{row_number}",
    )
    canonical_id = "_".join(
        [
            "BTED", id_token(source_id), id_token(sample), id_token(reference_name),
            "plus" if strand == "+" else "minus", id_token(position), f"r{row_number:06d}",
        ]
    )
    score = first_value(
        row,
        ["signal_or_score", "z_score", "score", "coverage", "intensity", "abundance", "base_mean", "conditions_detected", "log_average_read_count", "signal_at_published_coordinate"],
    )
    category = first_value(row, ["author_category", "category", "literature_category", "classification", "tts_class", "location_class"])
    gene = first_value(row, ["associated_gene_or_locus", "associated_gene", "locus", "upstream_gene", "gene_upstream", "locus_details", "gene_details"])
    coordinate_interpretation = first_value(
        row,
        ["coordinate_interpretation"],
        "Author/local table coordinate treated as 1-based biological position; BED is [position-1, position).",
    )
    return {
        "end_id": canonical_id,
        "source_id": source_id,
        "sample_id": sample,
        "assay": assay,
        "evidence_class": config["evidence"],
        "author_endpoint_id": author_id,
        "published_reference_accession": first_value(row, ["published_reference_accession"], reference_name),
        "reference_assembly": registry_row["reference_genome"],
        "reference_name": reference_name,
        "replicon_label": replicon,
        "biological_coordinate_1based": position,
        "bed_start_0based": str(int(position) - 1),
        "bed_end_0based": position,
        "strand": strand,
        "signal_or_score": score,
        "author_category": category,
        "associated_gene_or_locus": gene,
        "pmid": first_value(row, ["pmid"], registry_row["pmid"]),
        "doi": first_value(row, ["doi"], registry_row["doi"]),
        "source_table_or_file": first_value(row, ["source_table", "source_table_or_file"], Path(source_input_rel).name),
        "coordinate_interpretation": coordinate_interpretation,
        "original_row_reference": f"{source_input_rel}:row={row_number}",
        "qc_status": "migrated_coordinate_and_bed_checked",
        "note": config["note"],
    }


def validate_input_row(source_id: str, canonical: dict[str, str]) -> None:
    if canonical["evidence_class"] not in PUBLIC_EVIDENCE:
        raise ValueError(f"{source_id}: public evidence class is invalid: {canonical['evidence_class']}")
    try:
        position = int(canonical["biological_coordinate_1based"])
    except ValueError as exc:
        raise ValueError(f"{source_id}: non-integer coordinate: {canonical['biological_coordinate_1based']!r}") from exc
    if position < 1:
        raise ValueError(f"{source_id}: biological coordinate must be >= 1, got {position}")
    if canonical["strand"] not in {"+", "-"}:
        raise ValueError(f"{source_id}: invalid strand: {canonical['strand']!r}")
    if canonical["bed_start_0based"] != str(position - 1) or canonical["bed_end_0based"] != str(position):
        raise ValueError(f"{source_id}: BED conversion mismatch at {canonical['end_id']}")
    if canonical["reference_name"] == "NA":
        raise ValueError(f"{source_id}: reference_name is missing at {canonical['end_id']}")


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ENDPOINT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_bed(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(
                "\t".join(
                    [
                        row["reference_name"], row["bed_start_0based"], row["bed_end_0based"],
                        row["end_id"], "0", row["strand"],
                    ]
                ) + "\n"
            )


def processing_record_for(source_id: str, input_root: Path) -> Path | None:
    relative = PROCESSING_RECORDS.get(source_id)
    if not relative:
        return None
    candidate = input_root / relative
    return candidate if candidate.is_file() else None


def portable_processing_record(text: str) -> str:
    """Remove machine-specific executable/library paths from copied worklogs.

    The command intent (for example ``python3 import_...``) is useful
    provenance.  The user's Codex runtime path and local dynamic-library paths
    are not portable scientific provenance, so they are replaced by their
    environment-neutral equivalents before the record enters Git.
    """
    text = re.sub(
        r"/Users/[^\s`]+/python3",
        "python3",
        text,
    )
    text = text.replace("/opt/miniconda3/envs/batter-browser", "Conda environment `batter-browser`")
    text = text.replace("/usr/local/opt/xz/lib/liblzma.5.dylib", "a local xz dynamic library")
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def source_readme(
    manifest: dict[str, object],
    source_id: str,
    publication: dict[str, object],
    processing_record_present: bool,
) -> str:
    public_asset = publication.get("public_asset") or "无（仅审计）"
    public_records = publication.get("record_count", 0)
    evidence = publication.get("evidence_class") or "NA"
    status = publication["release_status"]
    return f"""# {source_id} — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `{status}` |
| 公开资产 | `{public_asset}` |
| 记录数 | {public_records} |
| 主要证据层 | `{evidence}` |
| 迁移日期 | {MIGRATION_DATE} |
| 参考组装 | `{manifest.get('reference_genome', 'NA')}` |
| 原始数据入口 | {manifest.get('raw_data_url', 'NA')} |
| 论文 | PMID [{manifest.get('pmid', 'NA')}](https://pubmed.ncbi.nlm.nih.gov/{manifest.get('pmid', '')}/) · DOI [{manifest.get('doi', 'NA')}]({manifest.get('doi_url', 'NA')}) |

## 范围与证据边界

{publication['decision_note']}

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。预测和作者混合实验/预测结果不进入 `data/public/`。详见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 可复现性材料

- 本来源原始测序与出版商工作簿不随 Git 复制；请通过上表的公共入口获取。
- 标准化输入/输出 SHA-256、行数和坐标检查结果写入本目录的 `manifest.json`。
- {'完整本地处理记录已作为 `processing_record.md` 随迁移保留。' if processing_record_present else '本次快照中没有独立的来源处理 Markdown；已保留来源 manifest 与发布判定，后续接入者必须补写详细处理记录。'}
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；它们属于大型衍生文件，后续应以有版本的外部发布物/浏览器包提供。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True, help="Local BGIRNA working-tree root")
    args = parser.parse_args()
    input_root = args.input_root.expanduser().resolve()
    if not (input_root / "data/source_registry/manifests").is_dir():
        parser.error("--input-root does not look like a BGIRNA working tree (manifests missing)")

    registry = read_registry()
    source_ids = sorted(registry)
    if source_ids != [f"BATTER_S1_{number:03d}" for number in range(1, 23)]:
        raise RuntimeError("Target registry must contain exactly BATTER_S1_001 through BATTER_S1_022")

    public_root = REPO_ROOT / "data/public/records"
    audit_root = REPO_ROOT / "data/audit/excluded_assets"
    source_doc_root = REPO_ROOT / "docs/sources"
    registry_manifest_root = REPO_ROOT / "data/registry/manifests"
    for path in (public_root, audit_root, source_doc_root, registry_manifest_root):
        path.mkdir(parents=True, exist_ok=True)

    publications: dict[str, dict[str, object]] = {}
    for source_id, config in PUBLIC_TABLES.items():
        source_input = input_root / config["input"]
        if not source_input.is_file():
            raise FileNotFoundError(f"{source_id}: missing input table: {source_input}")
        with source_input.open(encoding="utf-8", newline="") as handle:
            input_rows = list(csv.DictReader(handle, delimiter="\t"))
        if not input_rows:
            raise ValueError(f"{source_id}: input table is empty: {source_input}")

        canonical_rows: list[dict[str, str]] = []
        seen_ids: set[str] = set()
        for number, input_row in enumerate(input_rows, start=2):
            canonical = canonical_row(source_id, input_row, number, config, registry[source_id], config["input"])
            validate_input_row(source_id, canonical)
            if canonical["end_id"] in seen_ids:
                raise ValueError(f"{source_id}: duplicate canonical end_id {canonical['end_id']}")
            seen_ids.add(canonical["end_id"])
            canonical_rows.append(canonical)

        destination = public_root / source_id
        destination.mkdir(parents=True, exist_ok=True)
        tsv_path = destination / config["asset"]
        write_tsv(tsv_path, canonical_rows)
        files = [{"path": str(tsv_path.relative_to(REPO_ROOT)), "sha256": sha256(tsv_path)}]
        if config["evidence"] != "curated_record":
            bed_path = destination / f"{Path(config['asset']).stem}.bed"
            write_bed(bed_path, canonical_rows)
            files.append({"path": str(bed_path.relative_to(REPO_ROOT)), "sha256": sha256(bed_path)})
        publications[source_id] = {
            "release_status": "published_standardized",
            "public_asset": str(tsv_path.relative_to(REPO_ROOT)),
            "record_count": len(canonical_rows),
            "evidence_class": config["evidence"],
            "source_processed_table": config["input"],
            "source_processed_table_sha256": sha256(source_input),
            "files": files,
            "decision_note": config["note"],
        }

    for source_id in source_ids:
        if source_id not in publications:
            publications[source_id] = {
                "release_status": "audit_only",
                "public_asset": "",
                "record_count": 0,
                "evidence_class": "NA",
                "source_processed_table": "",
                "source_processed_table_sha256": "",
                "files": [],
                "decision_note": "No public endpoint table is emitted in this release. The local derived assets are described in an exclusion manifest until their evidence/provenance can be reconciled to the public schema.",
            }

    for source_id in source_ids:
        local_manifest = input_root / "data/source_registry/manifests" / f"{source_id}.json"
        if not local_manifest.is_file():
            raise FileNotFoundError(f"Missing local source manifest: {local_manifest}")
        manifest = json.loads(local_manifest.read_text(encoding="utf-8"))
        publication = publications[source_id]
        manifest["repository_release"] = {
            "release_version": "v0.1-local-snapshot",
            "migration_date": MIGRATION_DATE,
            "release_status": publication["release_status"],
            "public_asset": publication["public_asset"],
            "record_count": publication["record_count"],
            "evidence_class": publication["evidence_class"],
            "decision_note": publication["decision_note"],
            "jbrowse_published_in_repository": False,
        }
        if source_id in PUBLIC_TABLES:
            manifest["repository_release"]["source_processed_table"] = publication["source_processed_table"]
            manifest["repository_release"]["source_processed_table_sha256"] = publication["source_processed_table_sha256"]
            manifest["repository_release"]["published_file_checksums"] = publication["files"]
        target_manifest = registry_manifest_root / f"{source_id}.json"
        target_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        source_dir = source_doc_root / source_id
        source_dir.mkdir(parents=True, exist_ok=True)
        process_record = processing_record_for(source_id, input_root)
        (source_dir / "README.md").write_text(
            source_readme(manifest, source_id, publication, process_record is not None),
            encoding="utf-8",
        )
        if process_record is not None:
            (source_dir / "processing_record.md").write_text(
                portable_processing_record(process_record.read_text(encoding="utf-8")),
                encoding="utf-8",
            )

    for source_id, excluded_assets in AUDIT_ONLY.items():
        destination = audit_root / source_id
        destination.mkdir(parents=True, exist_ok=True)
        audit_rows = []
        for asset in excluded_assets:
            local_file = input_root / asset["local_path"]
            if not local_file.is_file():
                raise FileNotFoundError(f"{source_id}: missing excluded asset: {local_file}")
            with local_file.open(encoding="utf-8", newline="") as handle:
                row_count = sum(1 for _ in csv.reader(handle, delimiter="\t")) - 1
            audit_rows.append({
                **asset,
                "row_count": row_count,
                "sha256": sha256(local_file),
                "public_repository_copy": False,
            })
        payload = {
            "source_id": source_id,
            "migration_date": MIGRATION_DATE,
            "purpose": "Evidence-boundary audit manifest. The listed local files are intentionally not copied to data/public or the static website.",
            "excluded_assets": audit_rows,
        }
        (destination / "excluded_assets.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status_path = REPO_ROOT / "data/registry/batter_s1_publication_status.tsv"
    status_columns = [
        "source_id", "release_status", "public_asset", "record_count", "evidence_class",
        "reference_genome", "pmid", "coordinate_status", "decision_note",
    ]
    with status_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=status_columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for source_id in source_ids:
            publication = publications[source_id]
            source = registry[source_id]
            writer.writerow({
                "source_id": source_id,
                "release_status": publication["release_status"],
                "public_asset": publication["public_asset"] or "NA",
                "record_count": publication["record_count"],
                "evidence_class": publication["evidence_class"],
                "reference_genome": source["reference_genome"],
                "pmid": source["pmid"],
                "coordinate_status": source["coordinate_status"],
                "decision_note": publication["decision_note"],
            })

    release_manifest = {
        "release_version": "v0.1-local-snapshot",
        "migration_date": MIGRATION_DATE,
        "input_snapshot": "local BGIRNA working tree (not copied as a whole)",
        "summary": {
            "source_count": len(source_ids),
            "published_standardized_sources": sum(p["release_status"] == "published_standardized" for p in publications.values()),
            "audit_only_sources": sum(p["release_status"] == "audit_only" for p in publications.values()),
            "published_record_count": sum(int(p["record_count"]) for p in publications.values()),
            "jbrowse_assets_in_repository": 0,
        },
        "evidence_policy": "Prediction-only and author-integrated mixed-evidence tables are not copied to data/public or the site.",
        "sources": {source_id: publications[source_id] for source_id in source_ids},
    }
    release_path = REPO_ROOT / "data/public/release_manifest.v0.1-local-snapshot.json"
    release_path.write_text(json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"PASS  Built {release_path.relative_to(REPO_ROOT)}")
    print(f"      {release_manifest['summary']['published_standardized_sources']} public standardized sources; "
          f"{release_manifest['summary']['audit_only_sources']} audit-only source; "
          f"{release_manifest['summary']['published_record_count']} standardized records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
