"""Validate a BTED canonical release without writing a database.

The v0.2 release is the canonical source of truth for the first v0.3
milestone.  This module deliberately has no PostgreSQL dependency: it checks
the files that would be imported and produces a deterministic description of
the rows/keys that a future importer should insert.

Biological positions remain 1-based in the endpoint table.  BED is checked as
the half-open representation ``[position - 1, position)``.  No endpoint is
matched across contigs, and no evidence class is promoted during validation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


V02_ENDPOINT_COLUMNS = [
    "end_id",
    "source_id",
    "sample_id",
    "assay",
    "evidence_class",
    "author_endpoint_id",
    "published_reference_accession",
    "reference_assembly",
    "reference_name",
    "replicon_label",
    "biological_coordinate_1based",
    "bed_start_0based",
    "bed_end_0based",
    "strand",
    "signal_or_score",
    "author_category",
    "associated_gene_or_locus",
    "pmid",
    "doi",
    "source_table_or_file",
    "coordinate_interpretation",
    "original_row_reference",
    "qc_status",
    "note",
]

PUBLIC_EVIDENCE = frozenset(
    {"observed_signal", "called_endpoint", "author_called_endpoint", "curated_record"}
)
AUDIT_ONLY_SOURCE = "BATTER_S1_002"
PUBLISHED_STATUSES = frozenset({"published_standardized", "published"})
SOURCE_ID_RE = re.compile(r"^BATTER_S1_[0-9]{3}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RELEASE_VERSION_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
# Release assets are deliberately small, canonical tables/metadata.  Raw
# sequencing/alignment files must be represented by an external accession or a
# future separately governed asset, not silently added to this import plan.
MAX_CANONICAL_ASSET_BYTES = 50 * 1024 * 1024

# This small tracked table is generated from the existing v0.2 JBrowse release
# bundle.  It is provenance for the query/import plan only; the FASTA/FAI files
# themselves remain outside Git and are never loaded by this validator.
REFERENCE_CONTIG_COLUMNS = [
    "release_version",
    "assembly_accession",
    "contig_accession",
    "length_bp",
    "max_endpoint_position_1based",
    "supporting_source_ids",
    "fasta_asset_basename",
    "fasta_sha256",
    "fai_asset_basename",
    "fai_sha256",
    "bundle_sha256sums_sha256",
    "generator_version",
    "generated_at_utc",
]
DEFAULT_CONTIG_REGISTRY = "data/registry/reference_contigs.v0.2.0.tsv"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of *path* without loading it all in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


@dataclass(frozen=True)
class ValidationIssue:
    """A reproducible validation problem with an optional source and line."""

    message: str
    source_id: str | None = None
    file: str = ""
    line: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "file": self.file,
            "line": self.line,
            "message": self.message,
        }


@dataclass
class ValidationReport:
    """Structured result returned by :class:`CanonicalReleaseValidator`."""

    summary: dict[str, Any]
    plan: dict[str, Any]
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "plan": self.plan,
            "issues": [issue.as_dict() for issue in self.issues],
        }


class CanonicalReleaseValidator:
    """Validate one canonical release and build its deterministic import plan."""

    def __init__(
        self,
        release_root: str | Path,
        repo_root: str | Path | None = None,
        contig_registry: str | Path | None = None,
    ):
        self.release_root = Path(release_root).expanduser().resolve()
        if repo_root is None:
            # ``data/public/<release>`` is the standard layout.  For a custom
            # fixture callers should pass repo_root explicitly.
            self.repo_root = self.release_root.parents[2]
        else:
            self.repo_root = Path(repo_root).expanduser().resolve()
        if contig_registry is None:
            self.contig_registry_path = self.repo_root / DEFAULT_CONTIG_REGISTRY
        else:
            candidate = Path(contig_registry).expanduser()
            self.contig_registry_path = (
                candidate if candidate.is_absolute() else self.repo_root / candidate
            ).resolve()
        self.issues: list[ValidationIssue] = []
        self.checksums: dict[str, str] = {}
        self._registry_by_source: dict[str, dict[str, str]] = {}
        self._registry_manifests: dict[str, dict[str, Any]] = {}
        self._source_manifests: dict[str, dict[str, Any]] = {}
        self._release: dict[str, Any] = {}
        self._source_rows: dict[str, list[dict[str, str]]] = {}
        self._source_endpoints: dict[str, dict[str, dict[str, str]]] = {}
        self._source_annotations: dict[str, int] = {}
        self._annotation_end_ids: dict[str, set[str]] = {}
        # Kept only for the validated read-only export interface.  The
        # validator still uses the same rows for the foreign-key check; the
        # materializer needs the original fields so it can build a lossless
        # source_annotations JSON document without re-reading an unvalidated
        # file.
        self._source_annotation_rows: dict[str, list[dict[str, str]]] = {}
        self._source_annotation_fields: dict[str, list[str]] = {}
        self._contigs: set[tuple[str, str]] = set()
        self._contig_max_positions: dict[tuple[str, str], int] = {}
        self._contig_source_ids: dict[tuple[str, str], set[str]] = {}
        self._contig_registry: dict[tuple[str, str], dict[str, str]] = {}
        self._contig_registry_loaded = False
        self._contig_registry_ok = False
        self._samples: set[tuple[str, str]] = set()
        self._verified_assets: list[dict[str, Any]] = []
        self._declared_files: dict[str, dict[str, Path]] = {}
        self._declared_file_sha256: dict[str, dict[str, str]] = {}
        self._unresolved: list[str] = []

    def _display(self, path: Path) -> str:
        for base in (self.repo_root, self.release_root):
            try:
                return path.resolve().relative_to(base.resolve()).as_posix()
            except ValueError:
                continue
        return str(path)

    def _issue(
        self,
        message: str,
        source_id: str | None = None,
        path: Path | None = None,
        line: int | None = None,
    ) -> None:
        self.issues.append(
            ValidationIssue(
                message=message,
                source_id=source_id,
                file=self._display(path) if path is not None else "",
                line=line,
            )
        )

    def _read_tsv(self, path: Path, source_id: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                fields = list(reader.fieldnames or [])
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            self._issue(f"无法读取 TSV: {exc}", source_id, path, 1)
            return [], []
        return fields, rows

    def _record_root(self, entry: Mapping[str, Any]) -> Path:
        value = str(entry.get("record_root", ""))
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.repo_root / candidate
        return candidate

    def _file_from_record(self, record_root: Path, relative: str) -> Path:
        candidate = record_root / relative
        if candidate.exists():
            return candidate
        # This fallback makes compact fixtures possible when record_root is
        # relative to the release root rather than the repository root.
        candidate = self.release_root / relative
        if candidate.exists():
            return candidate
        return record_root / relative

    def _load_registry(self) -> None:
        path = self.repo_root / "data/registry/batter_s1_source_registry.tsv"
        if not path.is_file():
            self._issue("缺少来源 registry", path=path, line=1)
            return
        fields, rows = self._read_tsv(path)
        required = {
            "source_id",
            "species",
            "reference_genome",
            "pmid",
            "doi",
            "raw_data_accessions",
            "used_for_batter_augmentation",
        }
        missing = sorted(required - set(fields))
        if missing:
            self._issue(f"registry 缺少字段: {', '.join(missing)}", path=path, line=1)
        for number, row in enumerate(rows, start=2):
            source_id = row.get("source_id", "")
            if not SOURCE_ID_RE.fullmatch(source_id):
                self._issue("registry source_id 格式错误", source_id or None, path, number)
            if source_id in self._registry_by_source:
                self._issue("registry source_id 重复", source_id, path, number)
            self._registry_by_source[source_id] = row

    def _load_release(self) -> bool:
        path = self.release_root / "release_manifest.json"
        if not path.is_file():
            self._issue("缺少 release manifest", path=path, line=1)
            return False
        try:
            self._release = _json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            self._issue(f"release manifest 无法解析: {exc}", path=path, line=1)
            return False
        self.checksums[self._display(path)] = sha256_file(path)
        release_version = str(self._release.get("release_version", ""))
        if not release_version:
            self._issue("release_version 缺失", path=path, line=1)
        elif not RELEASE_VERSION_RE.fullmatch(release_version):
            self._issue(
                "release_version 必须符合 vMAJOR.MINOR.PATCH",
                path=path,
                line=1,
            )
        sources = self._release.get("sources")
        if not isinstance(sources, dict) or not sources:
            self._issue("release manifest 的 sources 必须为非空对象", path=path, line=1)
            return False
        return True

    def _load_registry_manifest(self, source_id: str) -> dict[str, Any] | None:
        path = self.repo_root / "data/registry/manifests" / f"{source_id}.json"
        if not path.is_file():
            self._issue("缺少 registry audit manifest", source_id, path, 1)
            return None
        try:
            value = _json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            self._issue(f"registry audit manifest 无法解析: {exc}", source_id, path, 1)
            return None
        self.checksums[self._display(path)] = sha256_file(path)
        self._registry_manifests[source_id] = value
        return value

    def _load_canonical_manifest(
        self,
        source_id: str,
        entry: Mapping[str, Any],
        resolved: Mapping[str, Path],
    ) -> tuple[dict[str, Any] | None, Path]:
        """Load the manifest inside the release record directory.

        The release-declared record manifest is canonical.  The registry JSON
        is loaded separately only for cross-audit and is never used as the
        source of release status/count/evidence.
        """

        record_root = self._record_root(entry)
        path = resolved.get("manifest.json", record_root / "manifest.json")
        if "manifest.json" not in resolved:
            self._issue(
                "release entry 必须声明 canonical manifest.json",
                source_id,
                path,
                1,
            )
        if not path.is_file():
            self._issue("缺少 canonical record manifest.json", source_id, path, 1)
            return None, path
        try:
            value = _json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            self._issue(f"canonical record manifest 无法解析: {exc}", source_id, path, 1)
            return None, path
        self._source_manifests[source_id] = value
        return value, path

    def _check_manifest_identity(
        self,
        source_id: str,
        entry: Mapping[str, Any],
        source_manifest: Mapping[str, Any] | None,
        path: Path,
    ) -> None:
        registry = self._registry_by_source.get(source_id, {})
        if source_manifest is None:
            return
        if source_manifest.get("source_id") != source_id:
            self._issue("来源 manifest source_id 不一致", source_id, path, 1)
        identity_keys = (
            "pmid",
            "doi",
            "species",
            "reference_genome",
            "paper_title",
            "published_year",
        )
        for key in identity_keys:
            expected = registry.get(key)
            actual = str(source_manifest.get(key, ""))
            if not actual.strip():
                self._issue(
                    f"来源 manifest 缺少必需身份字段: {key}",
                    source_id,
                    path,
                    1,
                )
            if expected and actual != expected:
                self._issue(
                    f"来源 manifest {key} 与 registry 不一致: {actual!r} != {expected!r}",
                    source_id,
                    path,
                    1,
                )
        release_version = str(self._release.get("release_version", ""))
        manifest_version = str(source_manifest.get("release_version", ""))
        if not manifest_version:
            self._issue(
                "来源 manifest 缺少必需身份字段: release_version",
                source_id,
                path,
                1,
            )
        elif manifest_version != release_version:
            self._issue(
                f"来源 manifest release_version 与根 release 不一致: {manifest_version!r} != {release_version!r}",
                source_id,
                path,
                1,
            )
        release_info = source_manifest.get("repository_release", {})
        if isinstance(release_info, dict):
            for key in ("release_status", "record_count", "evidence_class"):
                if key in release_info and str(release_info[key]) != str(entry.get(key)):
                    self._issue(
                        f"来源 manifest repository_release.{key} 与 release manifest 不一致",
                        source_id,
                        path,
                        1,
                    )
        for key in ("release_status", "record_count", "evidence_class"):
            if key in source_manifest and str(source_manifest[key]) != str(entry.get(key)):
                self._issue(
                    f"来源 manifest {key} 与 release manifest 不一致",
                    source_id,
                    path,
                    1,
                )
        if "source_annotations_status" in source_manifest and str(
            source_manifest["source_annotations_status"]
        ) != str(entry.get("source_annotations_status", "")):
            self._issue(
                "来源 manifest source_annotations_status 与 release manifest 不一致",
                source_id,
                path,
                1,
            )

    def _check_registry_audit_identity(
        self,
        source_id: str,
        canonical: Mapping[str, Any] | None,
        registry_manifest: Mapping[str, Any] | None,
        path: Path,
    ) -> None:
        """Cross-check the legacy registry manifest without using it as truth."""

        if registry_manifest is None or canonical is None:
            return
        for key in (
            "source_id",
            "pmid",
            "doi",
            "species",
            "reference_genome",
            "paper_title",
            "published_year",
        ):
            if key in registry_manifest and str(registry_manifest.get(key)) != str(canonical.get(key, "")):
                self._issue(
                    f"registry audit manifest {key} 与 canonical manifest 不一致",
                    source_id,
                    path,
                    1,
                )
    def _check_declared_files(
        self,
        source_id: str,
        entry: Mapping[str, Any],
        record_root: Path,
    ) -> dict[str, Path]:
        """Resolve and verify every file declared by a release source entry."""

        record_root = record_root.resolve()
        expected_root = (self.release_root / "records" / source_id).resolve()
        if record_root != expected_root:
            self._issue(
                "record_root 必须指向 release records/<source_id>，不能把 registry 或外部目录当作 canonical source",
                source_id,
                record_root,
                1,
            )
        resolved: dict[str, Path] = {}
        expected_sha256: dict[str, str] = {}
        files = entry.get("files", [])
        if not isinstance(files, list):
            self._issue("release manifest files 必须为数组", source_id, self.release_root / "release_manifest.json", 1)
            return resolved
        for item in files:
            if not isinstance(item, dict) or not item.get("path"):
                self._issue("release manifest 中存在无效文件项", source_id, self.release_root / "release_manifest.json", 1)
                continue
            relative = str(item["path"])
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                self._issue("release manifest 文件路径必须位于 record_root 内", source_id, self.release_root / "release_manifest.json", 1)
                continue
            if relative in resolved:
                self._issue("release manifest 文件路径重复", source_id, self.release_root / "release_manifest.json", 1)
                continue
            path = record_root / relative_path
            resolved[relative] = path
            expected_sha256[relative] = str(item.get("sha256", ""))
            try:
                path.resolve().relative_to(record_root)
            except ValueError:
                self._issue("release manifest 文件不能通过 symlink 越出 record_root", source_id, path, 1)
                continue
            if not path.is_file():
                self._issue(f"release manifest 声明的文件不存在: {relative}", source_id, path, 1)
                continue
            actual = sha256_file(path)
            self.checksums[f"{source_id}/{relative}"] = actual
            expected = expected_sha256[relative]
            if not SHA256_RE.fullmatch(expected):
                self._issue("声明文件缺少有效 64 位 SHA-256", source_id, path, 1)
            elif actual != expected:
                self._issue(
                    f"SHA-256 不匹配: expected={expected}, actual={actual}",
                    source_id,
                    path,
                    1,
                )
        self._declared_files[source_id] = resolved
        self._declared_file_sha256[source_id] = expected_sha256

        required = {"manifest.json", "fields.json", "SHA256SUMS.txt"}
        if entry.get("release_status") in PUBLISHED_STATUSES:
            required.update({"endpoints.tsv", "endpoints.bed"})
        if entry.get("source_annotations_status") == "published":
            required.add("source_annotations.tsv")
        for required_name in sorted(required):
            if required_name not in resolved:
                self._issue(
                    f"release entry 未声明必要文件: {required_name}",
                    source_id,
                    self.release_root / "release_manifest.json",
                    1,
                )
        sums_verified = self._check_sha256sums(source_id, record_root, resolved, expected_sha256)
        release_version = str(self._release.get("release_version", "release-unknown"))
        for relative, path in resolved.items():
            expected = expected_sha256.get(relative, "")
            if not path.is_file() or not SHA256_RE.fullmatch(expected):
                continue
            if relative != "SHA256SUMS.txt" and relative not in sums_verified:
                continue
            actual = sha256_file(path)
            if actual != expected:
                continue
            if path.stat().st_size > MAX_CANONICAL_ASSET_BYTES:
                self._unresolved.append(
                    f"asset {source_id}:{relative} exceeds {MAX_CANONICAL_ASSET_BYTES} bytes; omitted from import plan"
                )
                continue
            self._verified_assets.append(
                {
                    "asset_id": self._asset_id(release_version, source_id, relative),
                    "logical_path": self._display(path),
                    "source_id": source_id,
                    "asset_kind": self._asset_kind(relative),
                    "sha256": actual,
                    "byte_size": path.stat().st_size,
                    "is_public": True,
                }
            )
        return resolved

    @staticmethod
    def _asset_kind(relative: str) -> str:
        name = Path(relative).name
        if name == "SHA256SUMS.txt":
            return "checksum"
        if name == "endpoints.bed":
            return "bed"
        if name.endswith(".gff3"):
            return "gff3"
        if name.endswith(".fai"):
            return "fai"
        if name.endswith(".fa") or name.endswith(".fasta"):
            return "fasta"
        if name.endswith(".bw") or name.endswith(".bigwig"):
            return "bigwig"
        if name.endswith(".tbi"):
            return "tbi"
        if name.endswith(".config.json"):
            return "config"
        if name == "source_annotations.tsv":
            # The SQL schema deliberately keeps source-specific rows in the
            # metadata asset class; ``source_annotations`` is a table, not a
            # separate asset_kind enum.
            return "metadata"
        # manifest/fields/endpoints TSV and other small JSON/TSV files are
        # metadata in the database asset vocabulary.
        return "metadata"

    @staticmethod
    def _asset_id(release_version: str, source_id: str, relative: str) -> str:
        """Build a stable single-segment asset identifier for the API path."""

        def component(value: str) -> str:
            return re.sub(r"[^A-Za-z0-9._-]+", "_", value)

        return "--".join(component(value) for value in (release_version, source_id, relative))

    def _check_sha256sums(
        self,
        source_id: str,
        record_root: Path,
        resolved: Mapping[str, Path],
        expected_sha256: Mapping[str, str],
    ) -> set[str]:
        """Check the per-source SHA256SUMS file against files and manifest."""

        checksum_path = resolved.get("SHA256SUMS.txt")
        if checksum_path is None or not checksum_path.is_file():
            return set()
        entries: dict[str, str] = {}
        try:
            lines = checksum_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            self._issue(f"SHA256SUMS.txt 无法读取: {exc}", source_id, checksum_path, 1)
            return set()
        for number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2 or not SHA256_RE.fullmatch(parts[0]):
                self._issue("SHA256SUMS.txt 行格式错误", source_id, checksum_path, number)
                continue
            digest, relative = parts
            if relative in entries:
                self._issue("SHA256SUMS.txt 文件名重复", source_id, checksum_path, number)
            entries[relative] = digest
        declared_names = set(resolved)
        verified: set[str] = set()
        for relative, digest in entries.items():
            if relative not in declared_names:
                self._issue(
                    f"SHA256SUMS.txt 条目未在 release manifest 声明: {relative}",
                    source_id,
                    checksum_path,
                    line=1,
                )
                continue
            path = resolved[relative]
            if not path.is_file():
                continue
            actual = sha256_file(path)
            if actual != digest:
                self._issue(
                    f"SHA256SUMS 与实际文件不一致: {relative}",
                    source_id,
                    path,
                    1,
                )
                continue
            if expected_sha256.get(relative) != digest:
                self._issue(
                    f"SHA256SUMS 与 release manifest 声明不一致: {relative}",
                    source_id,
                    path,
                    1,
                )
                continue
            verified.add(relative)
        for relative in sorted(declared_names - {"SHA256SUMS.txt"}):
            if relative not in entries:
                self._issue(
                    f"release 文件未出现在 SHA256SUMS.txt: {relative}",
                    source_id,
                    checksum_path,
                    1,
                )
        return verified

    def _check_bed(
        self,
        source_id: str,
        endpoint_path: Path,
        bed_path: Path,
        rows: list[dict[str, str]],
    ) -> None:
        if not bed_path.is_file():
            self._issue("缺少 endpoints.bed", source_id, bed_path, 1)
            return
        try:
            with bed_path.open(encoding="utf-8") as handle:
                bed_rows = [line.rstrip("\n\r").split("\t") for line in handle if line.strip()]
        except (OSError, UnicodeError) as exc:
            self._issue(f"BED 无法读取: {exc}", source_id, bed_path, 1)
            return
        if len(bed_rows) != len(rows):
            self._issue(
                f"BED 行数 {len(bed_rows)} != endpoint 行数 {len(rows)}",
                source_id,
                bed_path,
                1,
            )
            return
        for number, (bed, row) in enumerate(zip(bed_rows, rows), start=1):
            expected = [
                row.get("reference_name", ""),
                row.get("bed_start_0based", ""),
                row.get("bed_end_0based", ""),
                row.get("end_id", ""),
                "0",
                row.get("strand", ""),
            ]
            if bed != expected:
                self._issue(
                    f"BED6 与 endpoints.tsv 不一致: expected={expected!r}, observed={bed!r}",
                    source_id,
                    bed_path,
                    number,
                )
                # One issue per first mismatch keeps CLI output useful for a
                # large release while still identifying the exact line.
                break

    def _check_endpoints(
        self,
        source_id: str,
        entry: Mapping[str, Any],
        endpoint_path: Path,
        bed_path: Path,
        source_manifest: Mapping[str, Any] | None,
    ) -> None:
        fields, rows = self._read_tsv(endpoint_path, source_id)
        if fields != V02_ENDPOINT_COLUMNS:
            self._issue(
                f"表头不是精确 24 列 schema: observed={fields!r}",
                source_id,
                endpoint_path,
                1,
            )
        self._source_rows[source_id] = rows
        try:
            expected_count = int(entry.get("record_count", -1))
        except (TypeError, ValueError):
            expected_count = -1
            self._issue("release manifest record_count 必须为整数", source_id, self.release_root / "release_manifest.json", 1)
        if len(rows) != expected_count:
            self._issue(
                f"行数 {len(rows)} != release manifest record_count {expected_count}",
                source_id,
                endpoint_path,
                1,
            )
        release_evidence = str(entry.get("evidence_class", ""))
        registry = self._registry_by_source.get(source_id, {})
        source_ids: set[str] = set()
        sample_ids: set[str] = set()
        endpoint_map: dict[str, dict[str, str]] = {}
        for number, row in enumerate(rows, start=2):
            end_id = row.get("end_id", "")
            row_source = row.get("source_id", "")
            sample_id = row.get("sample_id", "")
            source_ids.add(row_source)
            if row_source != source_id:
                self._issue("source_id 与来源不一致", source_id, endpoint_path, number)
            if not end_id or not end_id.startswith(f"BTED_{source_id}_"):
                self._issue("end_id 缺失或未保留 source 标识", source_id, endpoint_path, number)
            if end_id in endpoint_map:
                self._issue("end_id 重复", source_id, endpoint_path, number)
            endpoint_map[end_id] = row
            if not sample_id or sample_id == "NA":
                self._issue("sample_id 缺失；必须保留来源/样本上下文", source_id, endpoint_path, number)
            sample_ids.add(sample_id)
            evidence = row.get("evidence_class", "")
            if evidence not in PUBLIC_EVIDENCE:
                self._issue(f"不允许的公开 evidence_class: {evidence!r}", source_id, endpoint_path, number)
            if evidence != release_evidence:
                self._issue(
                    f"行 evidence_class 与 release manifest 不一致: {evidence!r} != {release_evidence!r}",
                    source_id,
                    endpoint_path,
                    number,
                )
            if row.get("strand") not in {"+", "-"}:
                self._issue("strand 必须为 + 或 -", source_id, endpoint_path, number)
            try:
                position = int(row.get("biological_coordinate_1based", ""))
                bed_start = int(row.get("bed_start_0based", ""))
                bed_end = int(row.get("bed_end_0based", ""))
            except ValueError:
                self._issue("坐标字段必须为整数", source_id, endpoint_path, number)
                continue
            if position < 1 or bed_start != position - 1 or bed_end != position:
                self._issue(
                    "1-based/BED 坐标转换错误；应为 start=position-1, end=position",
                    source_id,
                    endpoint_path,
                    number,
                )
            assembly = row.get("reference_assembly", "")
            contig = row.get("reference_name", "")
            if not assembly or assembly == "NA" or not contig or contig == "NA":
                self._issue("reference_assembly/reference_name 缺失", source_id, endpoint_path, number)
            contig_key = (assembly, contig)
            self._contigs.add(contig_key)
            self._contig_source_ids.setdefault(contig_key, set()).add(source_id)
            if position >= 1:
                self._contig_max_positions[contig_key] = max(
                    self._contig_max_positions.get(contig_key, 0), position
                )
            self._samples.add((source_id, sample_id))
            expected_pmid = registry.get("pmid", "")
            expected_doi = registry.get("doi", "")
            if expected_pmid and row.get("pmid") != expected_pmid:
                self._issue(
                    f"PMID 与 registry 不一致: {row.get('pmid')!r} != {expected_pmid!r}",
                    source_id,
                    endpoint_path,
                    number,
                )
            if expected_doi and row.get("doi") != expected_doi:
                self._issue(
                    f"DOI 与 registry 不一致: {row.get('doi')!r} != {expected_doi!r}",
                    source_id,
                    endpoint_path,
                    number,
                )
        self._source_endpoints[source_id] = endpoint_map
        if len(source_ids) > 1:
            self._issue("endpoint 文件混入多个 source_id", source_id, endpoint_path, 1)
        if source_manifest is not None:
            manifest_count = source_manifest.get("repository_release", {}).get("record_count")
            if manifest_count is not None:
                try:
                    manifest_count_int = int(manifest_count)
                except (TypeError, ValueError):
                    manifest_count_int = -1
                    self._issue("来源 manifest record_count 必须为整数", source_id, endpoint_path, 1)
                if manifest_count_int != len(rows):
                    self._issue(
                        f"行数 {len(rows)} != 来源 manifest record_count {manifest_count}",
                        source_id,
                        endpoint_path,
                        1,
                    )
        self._check_bed(source_id, endpoint_path, bed_path, rows)

    def _check_annotations(self, source_id: str, path: Path) -> None:
        fields, rows = self._read_tsv(path, source_id)
        if "end_id" not in fields:
            self._issue("source_annotations.tsv 缺少 end_id 外键列", source_id, path, 1)
            return
        endpoint_map = self._source_endpoints.get(source_id, {})
        source_registry = self._registry_by_source.get(source_id, {})
        for number, row in enumerate(rows, start=2):
            end_id = row.get("end_id", "")
            if end_id not in endpoint_map:
                self._issue(f"annotation end_id 无对应 endpoint: {end_id!r}", source_id, path, number)
            if row.get("source_id") and row["source_id"] != source_id:
                self._issue("annotation source_id 与来源不一致", source_id, path, number)
            if row.get("pmid") and source_registry.get("pmid") and row["pmid"] != source_registry["pmid"]:
                self._issue("annotation PMID 与 registry 不一致", source_id, path, number)
            if row.get("doi") and source_registry.get("doi") and row["doi"] != source_registry["doi"]:
                self._issue("annotation DOI 与 registry 不一致", source_id, path, number)
        self._source_annotation_fields[source_id] = list(fields)
        self._source_annotation_rows[source_id] = rows
        self._source_annotations[source_id] = len(rows)
        self._annotation_end_ids[source_id] = {
            row.get("end_id", "") for row in rows if row.get("end_id", "")
        }

    @staticmethod
    def _key_summary(values: Iterable[str]) -> dict[str, Any]:
        """Summarize a large deterministic key set without bloating JSON output."""

        ordered = sorted(set(values))
        digest = hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest()
        return {
            "count": len(ordered),
            "first": ordered[:3],
            "last": ordered[-3:] if len(ordered) > 3 else ordered,
            "sha256": digest,
        }

    def _check_source_set_and_metadata(self, source_ids: list[str]) -> None:
        """Check registry/release membership and shared publication/assembly facts."""

        release_set = set(source_ids)
        registry_set = set(self._registry_by_source)
        registry_path = self.repo_root / "data/registry/batter_s1_source_registry.tsv"
        for source_id in sorted(release_set - registry_set):
            self._issue("release source 在 registry 中缺失", source_id, registry_path, 1)
        for source_id in sorted(registry_set - release_set):
            self._issue("registry source 未出现在 release manifest", source_id, registry_path, 1)

        # Canonical record manifests are the import truth.  The legacy
        # registry manifests are included as an audit source here so that a
        # stale/edited copy cannot silently disagree when the same publication
        # or versioned assembly is shared by several sources.
        by_pmid: dict[str, list[tuple[str, str, Mapping[str, Any]]]] = {}
        by_assembly: dict[str, list[tuple[str, str, Mapping[str, Any]]]] = {}
        for source_id in source_ids:
            manifests: list[tuple[str, Mapping[str, Any]]] = []
            canonical = self._source_manifests.get(source_id)
            if canonical:
                manifests.append(("canonical", canonical))
            audit = self._registry_manifests.get(source_id)
            if audit:
                manifests.append(("registry_audit", audit))
            for kind, manifest in manifests:
                pmid = str(manifest.get("pmid", ""))
                assembly = str(manifest.get("reference_genome", ""))
                if pmid:
                    by_pmid.setdefault(pmid, []).append((source_id, kind, manifest))
                if assembly:
                    by_assembly.setdefault(assembly, []).append((source_id, kind, manifest))
        for pmid, members in by_pmid.items():
            signatures = {
                (
                    str(manifest.get("doi", "")),
                    str(manifest.get("paper_title", "")),
                    str(manifest.get("published_year", "")),
                )
                for _, _, manifest in members
            }
            if len(signatures) <= 1:
                continue
            for source_id, kind, _ in members:
                self._issue(
                    f"相同 PMID {pmid} 的 registry/canonical DOI/title/year 不一致",
                    source_id,
                    self._record_manifest_path(source_id)
                    if kind == "canonical"
                    else self.repo_root / "data/registry/manifests" / f"{source_id}.json",
                    1,
                )
        for assembly, members in by_assembly.items():
            species = {str(manifest.get("species", "")) for _, _, manifest in members}
            if len(species) <= 1:
                continue
            for source_id, kind, _ in members:
                self._issue(
                    f"相同带版本 assembly {assembly} 的 species 不一致",
                    source_id,
                    self._record_manifest_path(source_id)
                    if kind == "canonical"
                    else self.repo_root / "data/registry/manifests" / f"{source_id}.json",
                    1,
                )

    def _record_manifest_path(self, source_id: str) -> Path:
        entry = self._release.get("sources", {}).get(source_id, {})
        return self._record_root(entry) / "manifest.json"

    def _source_plan(self, source_ids: list[str]) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for source_id in source_ids:
            entry = self._release.get("sources", {}).get(source_id, {})
            rows.append(
                {
                    "source_id": source_id,
                    "release_status": entry.get("release_status"),
                    "record_count": len(self._source_rows.get(source_id, [])),
                    "sample_ids": sorted({sample for sid, sample in self._samples if sid == source_id}),
                    "endpoint_key_summary": self._key_summary(self._source_endpoints.get(source_id, {})),
                    "annotation_record_count": self._source_annotations.get(source_id, 0),
                    "has_jbrowse": bool(entry.get("has_jbrowse", False)),
                    "used_for_batter_augmentation": self._registry_by_source.get(source_id, {}).get(
                        "used_for_batter_augmentation"
                    ),
                }
            )
        return {"row_count": len(rows), "keys": [row["source_id"] for row in rows], "rows": rows}

    def _accession_namespace(self, accession: str, source_id: str) -> tuple[str | None, str | None]:
        """Map only the explicitly supported accession prefixes."""

        upper = accession.upper()
        if upper.startswith("GSE"):
            return "GEO", None
        if upper.startswith("SR") or upper.startswith("PRJNA"):
            return "SRA", None
        if upper.startswith("PRJEB"):
            return "ENA", None
        if upper.startswith("E-MTAB"):
            return "BioStudies", "ArrayExpress"
        message = f"unknown accession namespace for {source_id}:{accession}"
        if message not in self._unresolved:
            self._unresolved.append(message)
        return None, None

    def _load_contig_registry(self) -> None:
        """Load and validate the small reference-contig provenance table.

        The table is generated from the already published v0.2 JBrowse bundle
        by ``scripts/build_reference_contig_registry.py``.  It is intentionally
        not a substitute for the FASTA/FAI files: the builder has verified
        those files and records their checksums here.  Missing provenance keeps
        the canonical release valid but prevents a future PostgreSQL import.
        """

        path = self.contig_registry_path
        if not path.is_file():
            message = f"reference contig registry missing: {self._display(path)}"
            if message not in self._unresolved:
                self._unresolved.append(message)
            return

        self._contig_registry_loaded = True
        self.checksums[self._display(path)] = sha256_file(path)
        issue_start = len(self.issues)
        fields, rows = self._read_tsv(path)
        missing_fields = sorted(set(REFERENCE_CONTIG_COLUMNS) - set(fields))
        extra_fields = sorted(set(fields) - set(REFERENCE_CONTIG_COLUMNS))
        if fields != REFERENCE_CONTIG_COLUMNS:
            details: list[str] = []
            if missing_fields:
                details.append(f"missing={','.join(missing_fields)}")
            if extra_fields:
                details.append(f"extra={','.join(extra_fields)}")
            if not details:
                details.append("column order differs")
            self._issue(
                f"reference contig registry header must match exact schema ({'; '.join(details)})",
                path=path,
                line=1,
            )
        if missing_fields:
            self._unresolved.append(
                f"reference contig registry cannot be parsed because required fields are missing: {','.join(missing_fields)}"
            )
            return

        release_version = str(self._release.get("release_version", ""))
        seen: set[tuple[str, str]] = set()
        bundle_checksum_values: set[str] = set()
        for number, row in enumerate(rows, start=2):
            assembly = str(row.get("assembly_accession", "")).strip()
            contig = str(row.get("contig_accession", "")).strip()
            if not assembly or assembly == "NA" or not contig or contig == "NA":
                self._issue("reference contig registry assembly/contig 缺失", path=path, line=number)
                continue
            key = (assembly, contig)
            if key in seen:
                self._issue(
                    f"reference contig registry assembly/contig 重复: {assembly}/{contig}",
                    path=path,
                    line=number,
                )
                continue
            seen.add(key)
            valid = True
            if str(row.get("release_version", "")) != release_version:
                self._issue(
                    f"reference contig registry release_version 与根 release 不一致: {row.get('release_version')!r} != {release_version!r}",
                    path=path,
                    line=number,
                )
                valid = False
            try:
                length_bp = int(str(row.get("length_bp", "")))
                max_position = int(str(row.get("max_endpoint_position_1based", "")))
            except (TypeError, ValueError):
                self._issue(
                    "reference contig registry length/max endpoint 必须为整数",
                    path=path,
                    line=number,
                )
                valid = False
                length_bp = 0
                max_position = 0
            if length_bp <= 0:
                self._issue("reference contig registry length_bp 必须为正数", path=path, line=number)
                valid = False
            if max_position <= 0:
                self._issue(
                    "reference contig registry max_endpoint_position_1based 必须为正数",
                    path=path,
                    line=number,
                )
                valid = False
            if length_bp > 0 and max_position > 0 and length_bp < max_position:
                self._issue(
                    f"reference contig length_bp 必须大于或等于 max endpoint position: {length_bp} < {max_position}",
                    path=path,
                    line=number,
                )
                valid = False

            actual_max = self._contig_max_positions.get(key)
            if actual_max is None:
                self._issue(
                    f"reference contig registry contains extra assembly/contig: {assembly}/{contig}",
                    path=path,
                    line=number,
                )
                valid = False
            else:
                if max_position != actual_max:
                    self._issue(
                        f"reference contig registry max endpoint 不匹配 canonical endpoints: {max_position} != {actual_max}",
                        path=path,
                        line=number,
                    )
                    valid = False
                if length_bp < actual_max:
                    self._issue(
                        f"reference contig length_bp 不足以覆盖 canonical endpoint: {length_bp} < {actual_max}",
                        path=path,
                        line=number,
                    )
                    valid = False

            support_values = [item.strip() for item in str(row.get("supporting_source_ids", "")).split(";") if item.strip()]
            support_set = set(support_values)
            expected_support = self._contig_source_ids.get(key, set())
            if not support_values or any(not SOURCE_ID_RE.fullmatch(item) for item in support_values):
                self._issue(
                    "reference contig registry supporting_source_ids 格式错误",
                    path=path,
                    line=number,
                )
                valid = False
            if len(support_values) != len(support_set):
                self._issue(
                    "reference contig registry supporting_source_ids 不得重复",
                    path=path,
                    line=number,
                )
                valid = False
            if support_values != sorted(support_values):
                self._issue(
                    "reference contig registry supporting_source_ids 必须按 source_id 排序",
                    path=path,
                    line=number,
                )
                valid = False
            if support_set != expected_support:
                self._issue(
                    f"reference contig registry supporting_source_ids 与 endpoint 来源不一致: {sorted(support_set)} != {sorted(expected_support)}",
                    path=path,
                    line=number,
                )
                valid = False

            for field_name in (
                "fasta_asset_basename",
                "fai_asset_basename",
                "generator_version",
                "generated_at_utc",
            ):
                value = str(row.get(field_name, "")).strip()
                if not value or "/" in value or "\\" in value or value in {".", ".."}:
                    self._issue(
                        f"reference contig registry {field_name} 无效",
                        path=path,
                        line=number,
                    )
                    valid = False
                if field_name == "generated_at_utc" and value:
                    try:
                        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        timestamp = None
                    if timestamp is None or timestamp.tzinfo is None:
                        self._issue(
                            "reference contig registry generated_at_utc 必须为带时区的 ISO-8601 时间",
                            path=path,
                            line=number,
                        )
                        valid = False
            for field_name in ("fasta_sha256", "fai_sha256", "bundle_sha256sums_sha256"):
                value = str(row.get(field_name, "")).strip()
                if not SHA256_RE.fullmatch(value):
                    self._issue(
                        f"reference contig registry {field_name} 必须为 64 位小写 SHA-256",
                        path=path,
                        line=number,
                    )
                    valid = False
                if field_name == "bundle_sha256sums_sha256" and SHA256_RE.fullmatch(value):
                    bundle_checksum_values.add(value)
            if valid:
                self._contig_registry[key] = row

        expected_keys = set(self._contigs)
        actual_keys = set(seen)
        for assembly, contig in sorted(expected_keys - actual_keys):
            self._issue(
                f"reference contig registry missing endpoint contig: {assembly}/{contig}",
                path=path,
                line=1,
            )
        for assembly, contig in sorted(actual_keys - expected_keys):
            self._issue(
                f"reference contig registry extra contig: {assembly}/{contig}",
                path=path,
                line=1,
            )

        if len(bundle_checksum_values) > 1:
            self._issue(
                "reference contig registry rows reference more than one bundle SHA256SUMS checksum",
                path=path,
                line=1,
            )

        if len(self.issues) == issue_start and actual_keys == expected_keys:
            self._contig_registry_ok = True
        else:
            message = f"reference contig registry validation failed: {self._display(path)}"
            if message not in self._unresolved:
                self._unresolved.append(message)

    def _build_plan(
        self,
        source_ids: list[str],
        release_sha256: str,
        validation_status: str,
    ) -> dict[str, Any]:
        registry_rows = [self._registry_by_source[sid] for sid in source_ids if sid in self._registry_by_source]
        publication_by_pmid: dict[str, dict[str, Any]] = {}
        for sid in source_ids:
            manifest = self._source_manifests.get(sid, {})
            registry = self._registry_by_source.get(sid, {})
            pmid = str(manifest.get("pmid") or registry.get("pmid", ""))
            if not pmid:
                continue
            publication_by_pmid.setdefault(
                pmid,
                {
                    "pmid": pmid,
                    "doi": str(manifest.get("doi", registry.get("doi", ""))),
                    "paper_title": str(manifest.get("paper_title", "")),
                    "published_year": manifest.get("published_year"),
                },
            )
        publications = [publication_by_pmid[pmid] for pmid in sorted(publication_by_pmid)]
        assemblies = sorted({row.get("reference_genome", "") for row in registry_rows if row.get("reference_genome")})
        contigs: list[dict[str, Any]] = []
        for assembly, contig in sorted(self._contigs):
            registry_row = self._contig_registry.get((assembly, contig), {})
            item: dict[str, Any] = {
                "assembly": assembly,
                "contig": contig,
                "length_bp": (
                    int(registry_row["length_bp"])
                    if registry_row.get("length_bp", "").isdigit()
                    else None
                ),
            }
            for field_name in (
                "max_endpoint_position_1based",
                "supporting_source_ids",
                "fasta_asset_basename",
                "fasta_sha256",
                "fai_asset_basename",
                "fai_sha256",
                "bundle_sha256sums_sha256",
                "generator_version",
                "generated_at_utc",
            ):
                if field_name in registry_row:
                    value = registry_row[field_name]
                    if field_name == "max_endpoint_position_1based" and str(value).isdigit():
                        value = int(value)
                    item[field_name] = value
            contigs.append(item)
        samples = sorted(
            [{"source_id": sid, "sample_id": sample} for sid, sample in self._samples],
            key=lambda x: (x["source_id"], x["sample_id"]),
        )
        accessions: list[dict[str, Any]] = []
        for sid in source_ids:
            value = self._registry_by_source.get(sid, {}).get("raw_data_accessions", "")
            for accession in sorted({part.strip() for part in value.split(";") if part.strip()}):
                namespace, alias = self._accession_namespace(accession, sid)
                item: dict[str, Any] = {
                    "source_id": sid,
                    "accession_namespace": namespace,
                    "accession": accession,
                    "raw_value": accession,
                    "accession_type": "study",
                    "ordinal": sorted(
                        {part.strip() for part in value.split(";") if part.strip()}
                    ).index(accession)
                    + 1,
                }
                if alias:
                    item["metadata"] = {"namespace_alias": alias}
                accessions.append(item)
        annotation_rows = sum(self._source_annotations.values())
        unresolved = list(self._unresolved)
        if contigs and not self._contig_registry_ok:
            if self._contig_registry_loaded:
                message = (
                    f"length/provenance for {len(contigs)} contigs is not validated; "
                    "resolve the tracked reference contig registry before PostgreSQL import"
                )
            else:
                message = (
                    f"length_bp is not present for {len(contigs)} contigs; "
                    "resolve the cited reference FASTA before PostgreSQL import"
                )
            if message not in unresolved:
                unresolved.insert(0, message)
        asset_rows = sorted(self._verified_assets, key=lambda row: row["asset_id"])
        postgresql_ready = validation_status == "validated" and not unresolved
        plan = {
            "plan_version": "0.3.0-import-plan-1",
            "write_mode": "not_written",
            "canonical_validation_status": validation_status,
            "postgresql_ready": postgresql_ready,
            "release_version": self._release.get("release_version"),
            "canonical_manifest": {
                "path": self._display(self.release_root / "release_manifest.json"),
                "sha256": release_sha256,
            },
            "tables": {
                "release_versions": {"row_count": 1, "keys": [self._release.get("release_version")]},
                "import_runs": {
                    "row_count": 1,
                    "keys": [
                        {
                            "release_version": self._release.get("release_version"),
                            "input_manifest_sha256": release_sha256,
                        }
                    ],
                    "run_status": validation_status,
                },
                "publications": {
                    "row_count": len(publications),
                    "keys": [row["pmid"] for row in publications],
                    "rows": publications,
                },
                "assemblies": {"row_count": len(assemblies), "keys": assemblies},
                "contigs": {"row_count": len(contigs), "keys": contigs, "rows": contigs},
                "sources": self._source_plan(source_ids),
                "source_accessions": {"row_count": len(accessions), "keys": accessions},
                "samples": {"row_count": len(samples), "keys": samples},
                "endpoints": {
                    "row_count": sum(len(rows) for rows in self._source_rows.values()),
                    "key_summary": self._key_summary(
                        end_id
                        for endpoint_map in self._source_endpoints.values()
                        for end_id in endpoint_map
                    ),
                },
                "source_annotations": {
                    "table_count": len(self._source_annotations),
                    "row_count": annotation_rows,
                    "key_summary": self._key_summary(
                        end_id
                        for source_id in self._annotation_end_ids
                        for end_id in self._annotation_end_ids[source_id]
                    ),
                },
                "genes": {"row_count": 0, "keys": []},
                "endpoint_gene_context": {"row_count": 0, "keys": []},
                "assets": {"row_count": len(asset_rows), "keys": asset_rows},
            },
            "unresolved": unresolved,
        }
        return plan

    def export_snapshot(self) -> dict[str, Any]:
        """Return a validated, read-only snapshot for downstream materializers.

        This is intentionally the only public escape hatch for the canonical
        rows.  It can only be called after :meth:`validate` has completed
        successfully *and* the reference-contig provenance gate is satisfied.
        Callers therefore cannot accidentally materialize a failed release or
        one whose PostgreSQL ``contigs.length_bp`` values are unresolved.
        The returned dictionaries/lists are deep copies so a caller cannot
        mutate the validator's state and then re-use it as evidence.
        """

        report = getattr(self, "_last_report", None)
        if report is None:
            raise RuntimeError("validate() must be called before export_snapshot()")
        if not report.ok:
            raise ValueError("cannot export a snapshot from a failed canonical validation")
        if not report.plan.get("postgresql_ready", False):
            raise ValueError("cannot export a snapshot while PostgreSQL readiness is unresolved")
        import copy

        return copy.deepcopy(
            {
                "release": self._release,
                "release_root": str(self.release_root),
                "repo_root": str(self.repo_root),
                "contig_registry_path": str(self.contig_registry_path),
                "source_ids": sorted(self._source_manifests),
                "source_manifests": self._source_manifests,
                "registry_rows": self._registry_by_source,
                "registry_manifests": self._registry_manifests,
                "source_rows": self._source_rows,
                "source_annotation_rows": self._source_annotation_rows,
                "source_annotation_fields": self._source_annotation_fields,
                "contig_registry": {
                    f"{assembly}\t{contig}": row
                    for (assembly, contig), row in self._contig_registry.items()
                },
                "contigs": sorted(self._contigs),
                "samples": sorted(self._samples),
                "verified_assets": self._verified_assets,
                "declared_files": {
                    source_id: {name: str(path) for name, path in files.items()}
                    for source_id, files in self._declared_files.items()
                },
                "declared_file_sha256": self._declared_file_sha256,
                "checksums": self.checksums,
                "report": report.as_dict(),
            }
        )

    def validate(self) -> ValidationReport:
        release_path = self.release_root / "release_manifest.json"
        if not self._load_release():
            summary = {
                "release_version": None,
                "canonical_validation_status": "failed",
                "postgresql_ready": False,
                "source_count": 0,
                "published_standardized_sources": 0,
                "audit_only_sources": 0,
                "published_record_count": 0,
                "augmentation_true": 0,
                "augmentation_false": 0,
                "publication_count": 0,
                "assembly_count": 0,
                "contig_count": 0,
                "sample_count": 0,
                "source_accession_count": 0,
                "source_annotation_table_count": 0,
                "source_annotation_record_count": 0,
                "input_checksums": self.checksums,
                "unresolved": [],
            }
            report = ValidationReport(
                summary,
                {
                    "write_mode": "not_written",
                    "canonical_validation_status": "failed",
                    "postgresql_ready": False,
                },
                self.issues,
            )
            self._last_report = report
            return report
        self._load_registry()
        sources = self._release.get("sources", {})
        # Do not let JSON object insertion order affect the import plan.
        source_ids = sorted(sources) if isinstance(sources, dict) else []
        if not source_ids:
            source_ids = sorted(self._registry_by_source)
        release_version = str(self._release.get("release_version", ""))
        release_summary = self._release.get("summary", {})
        if not isinstance(release_summary, dict):
            release_summary = {}
            self._issue("release manifest summary 必须为对象", path=release_path, line=1)
        public_count = 0
        audit_count = 0
        augmentation_true = 0
        augmentation_false = 0
        for source_id in source_ids:
            if not SOURCE_ID_RE.fullmatch(source_id):
                self._issue("release manifest source_id 格式错误", source_id, release_path, 1)
            entry = sources.get(source_id, {})
            if not isinstance(entry, dict):
                self._issue("source entry 必须为对象", source_id, release_path, 1)
                continue
            if entry.get("release_status") in PUBLISHED_STATUSES:
                public_count += 1
            elif entry.get("release_status") == "audit_only":
                audit_count += 1
            registry = self._registry_by_source.get(source_id)
            if registry is None:
                self._issue("registry 中缺少 source", source_id, self.repo_root / "data/registry/batter_s1_source_registry.tsv", 1)
            else:
                flag = registry.get("used_for_batter_augmentation", "")
                if flag == "TRUE":
                    augmentation_true += 1
                elif flag == "FALSE":
                    augmentation_false += 1
                else:
                    self._issue(f"augmentation flag 必须为 TRUE/FALSE: {flag!r}", source_id, self.repo_root / "data/registry/batter_s1_source_registry.tsv", 1)
            record_root = self._record_root(entry)
            resolved = self._check_declared_files(source_id, entry, record_root)
            source_manifest, source_manifest_path = self._load_canonical_manifest(source_id, entry, resolved)
            registry_manifest_path = self.repo_root / "data/registry/manifests" / f"{source_id}.json"
            registry_manifest = self._load_registry_manifest(source_id)
            self._check_manifest_identity(source_id, entry, source_manifest, source_manifest_path)
            self._check_registry_audit_identity(
                source_id,
                source_manifest,
                registry_manifest,
                registry_manifest_path,
            )
            if (
                source_manifest is not None
                and source_manifest.get("source_annotations_status") == "published"
                and "source_annotations.tsv" not in resolved
            ):
                self._issue(
                    "canonical manifest source_annotations_status=published 但 release entry 未声明 source_annotations.tsv",
                    source_id,
                    self.release_root / "release_manifest.json",
                    1,
                )
            endpoint_path = resolved.get("endpoints.tsv", self._file_from_record(record_root, "endpoints.tsv"))
            bed_path = resolved.get("endpoints.bed", self._file_from_record(record_root, "endpoints.bed"))
            status = entry.get("release_status")
            if status == "audit_only":
                if entry.get("record_count") != 0:
                    self._issue("audit_only 必须 record_count=0", source_id, release_path, 1)
                if entry.get("has_jbrowse"):
                    self._issue("audit_only 不得有 JBrowse", source_id, release_path, 1)
                if endpoint_path.is_file():
                    self._issue("audit_only 不得存在 endpoints.tsv", source_id, endpoint_path, 1)
                if any(record_root.glob("*jbrowse*")) or any(record_root.glob("*.config.json")):
                    self._issue("audit_only 不得有 JBrowse 配置", source_id, record_root, 1)
                continue
            if status not in PUBLISHED_STATUSES:
                self._issue(f"无法识别 release_status: {status!r}", source_id, release_path, 1)
                continue
            if not endpoint_path.is_file():
                self._issue("published source 缺少 endpoints.tsv", source_id, endpoint_path, 1)
                continue
            if not entry.get("has_jbrowse", False):
                self._issue("published source 必须 has_jbrowse=true", source_id, release_path, 1)
            self._check_endpoints(source_id, entry, endpoint_path, bed_path, source_manifest)
            annotation_path = resolved.get("source_annotations.tsv", self._file_from_record(record_root, "source_annotations.tsv"))
            annotation_status = str(entry.get("source_annotations_status", ""))
            if annotation_path.is_file():
                self._check_annotations(source_id, annotation_path)
            elif annotation_status == "published":
                self._issue("source_annotations_status=published 但缺少 source_annotations.tsv", source_id, annotation_path, 1)
        actual_public_rows = sum(len(rows) for rows in self._source_rows.values())
        self._check_source_set_and_metadata(source_ids)
        # Resolve reference lengths only after all endpoint pairs and their
        # source provenance have been collected.  A missing registry is an
        # unresolved query-layer prerequisite, not a canonical-release error.
        self._load_contig_registry()
        expected_summary = {
            "source_count": len(source_ids),
            "published_standardized_sources": public_count,
            "audit_only_sources": audit_count,
            "published_record_count": actual_public_rows,
        }
        for key, actual in expected_summary.items():
            declared = release_summary.get(key)
            if declared != actual:
                self._issue(
                    f"release summary {key}={declared!r} 与实际 {actual!r} 不一致",
                    path=release_path,
                    line=1,
                )
        release_sha256 = self.checksums.get(self._display(release_path), sha256_file(release_path))
        plan = self._build_plan(
            source_ids,
            release_sha256,
            "validated" if not self.issues else "failed",
        )
        summary = {
            "release_version": release_version,
            "canonical_validation_status": plan["canonical_validation_status"],
            "postgresql_ready": plan["postgresql_ready"],
            "source_count": len(source_ids),
            "published_standardized_sources": public_count,
            "audit_only_sources": audit_count,
            "published_record_count": actual_public_rows,
            "augmentation_true": augmentation_true,
            "augmentation_false": augmentation_false,
            "publication_count": plan["tables"]["publications"]["row_count"],
            "assembly_count": plan["tables"]["assemblies"]["row_count"],
            "contig_count": plan["tables"]["contigs"]["row_count"],
            "sample_count": plan["tables"]["samples"]["row_count"],
            "source_accession_count": plan["tables"]["source_accessions"]["row_count"],
            "source_annotation_table_count": plan["tables"]["source_annotations"]["table_count"],
            "source_annotation_record_count": plan["tables"]["source_annotations"]["row_count"],
            "input_checksums": dict(sorted(self.checksums.items())),
            "unresolved": list(plan.get("unresolved", [])),
        }
        report = ValidationReport(summary, plan, self.issues)
        self._last_report = report
        return report


def validate_release(
    release_root: str | Path = "data/public/v0.2.0",
    repo_root: str | Path | None = None,
    contig_registry: str | Path | None = None,
) -> ValidationReport:
    """Validate a release and return a :class:`ValidationReport`."""

    return CanonicalReleaseValidator(
        release_root,
        repo_root=repo_root,
        contig_registry=contig_registry,
    ).validate()
