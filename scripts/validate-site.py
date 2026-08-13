#!/usr/bin/env python3
"""BTED GitHub Pages 静态演示站点安全验证脚本。

对站点产物目录（默认 site/）执行以下检查，任一检查失败即以退出码 1 结束：

1. 文件类型与体积：无 FASTQ、xlsx、zip 等原始/大型数据文件；单文件不超过 1 MiB。
2. 绝对路径：无根相对链接（href="/..."）、无 file:// 与本地文件系统路径。
3. 凭据扫描：无 API key、密码、令牌等占位或真实凭据格式。
4. 证据标签：无未经批准的证据标签（如 "experimentally validated" / "实验验证"）。
5. 内部链接完整性：HTML 中的相对链接必须能解析到产物内的真实文件。

用法：
    python3 scripts/validate-site.py [站点目录]   # 默认 site/
"""

from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

MAX_FILE_BYTES = 1024 * 1024  # 1 MiB；站点页面与样式均为 KB 级
MAX_JBROWSE_FILE_BYTES = 64 * 1024 * 1024
MAX_DOWNLOAD_FILE_BYTES = 4 * 1024 * 1024

# 原始测序数据、出版商工作簿、压缩包、坐标/比对文件一律不得进入站点产物
FORBIDDEN_EXTENSIONS = {
    ".fastq", ".fq", ".gz", ".sra",
    ".xlsx", ".xls", ".ods",
    ".zip", ".tar", ".tgz", ".bz2", ".xz", ".7z", ".rar",
    ".bam", ".sam", ".cram",
    ".bed", ".gff", ".gff3", ".gtf", ".vcf", ".bcf",
    ".wig", ".bw", ".bigwig",
    ".fa", ".fasta", ".fna",
}

# The staged Pages artifact may contain the separately released JBrowse bundle.
# These file types remain forbidden in the checked-in ``site/`` source, but are
# expected under ``jbrowse/`` after the versioned asset is unpacked.
ALLOWED_JBROWSE_SUFFIXES = {
    ".html", ".css", ".js", ".json", ".txt", ".ico",
    ".fna", ".fai", ".bed", ".bw", ".gff3", ".gff3.gz", ".tbi", ".ix", ".ixx",
}
ALLOWED_DOWNLOAD_SUFFIXES = {".tsv", ".bed", ".json", ".txt"}

TEXT_EXTENSIONS = {".html", ".htm", ".css", ".js", ".json", ".xml", ".txt", ".md", ".svg"}

# 绝对路径 / 根相对链接 / 本地文件系统路径
ABSOLUTE_PATH_PATTERNS = [
    (re.compile(r"""(?:href|src|action)\s*=\s*["']/(?!/)""", re.IGNORECASE),
     "根相对链接（href=\"/...\"），GitHub Pages 项目子路径下会失效"),
    (re.compile(r"""url\(\s*["']?/(?!/)""", re.IGNORECASE),
     "CSS 根相对资源引用（url(/...)）"),
    (re.compile(r"""(?:href|src)\s*=\s*["']//""", re.IGNORECASE),
     "协议相对 URL（//...），应使用显式 https://"),
    (re.compile(r"file://", re.IGNORECASE), "file:// 本地文件引用"),
    (re.compile(r"(?:/Users/|/home/|/opt/|/var/|/tmp/|/private/)[^\s\"'<)]*"),
     "本地文件系统绝对路径"),
    (re.compile(r"[A-Za-z]:\\\\[^\s\"'<)]+"), "Windows 本地路径"),
]

# 凭据 / 密钥 / 口令占位
SECRET_PATTERNS = [
    (re.compile(r"\bapi[_-]?key\b", re.IGNORECASE), "API key 字样"),
    (re.compile(r"\bpassword\b", re.IGNORECASE), "password 字样"),
    (re.compile(r"\bpasswd\b", re.IGNORECASE), "passwd 字样"),
    (re.compile(r"\bsecret\b", re.IGNORECASE), "secret 字样"),
    (re.compile(r"\baccess[_-]?token\b", re.IGNORECASE), "access token 字样"),
    (re.compile(r"\bauth[_-]?token\b", re.IGNORECASE), "auth token 字样"),
    (re.compile(r"\bbearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE), "Bearer 令牌"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "PEM 私钥"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS Access Key ID"),
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"), "GitHub personal access token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "GitHub fine-grained token"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack token"),
    (re.compile(r"\byour[_-]?(api[_-]?key|token|password|secret)\b", re.IGNORECASE),
     "凭据占位符（YOUR_...）"),
]

# 未经批准的证据标签（骨架阶段一律禁止出现，包括否定语境，以免被误读）
FORBIDDEN_LABEL_PATTERNS = [
    (re.compile(r"experimentally\s+validated", re.IGNORECASE), "未批准证据标签"),
    (re.compile(r"experimentally\s+verified", re.IGNORECASE), "未批准证据标签"),
    (re.compile(r"experimentally\s+confirmed", re.IGNORECASE), "未批准证据标签"),
    (re.compile(r"experimental\s+validation", re.IGNORECASE), "未批准证据标签"),
    (re.compile(r"validated\s+terminator", re.IGNORECASE), "未批准证据标签"),
    (re.compile(r"confirmed\s+terminator", re.IGNORECASE), "未批准证据标签"),
    (re.compile(r"实验验证"), "未批准证据标签"),
    (re.compile(r"实验证实"), "未批准证据标签"),
    (re.compile(r"经实验确认"), "未批准证据标签"),
]

REQUIRED_FILES = ["index.html", "sources.html", "catalog.html", "methodology.html", "about.html", "css/style.css"]


class LinkCollector(HTMLParser):
    """收集 HTML 中的 href/src 引用，用于相对链接完整性检查。"""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[int, str, str]] = []  # (行号, 属性, 值)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in ("href", "src", "action") and value:
                self.links.append((self.getpos()[0], name, value))


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def scan_text(path: Path, rel: str, problems: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, ValueError):
        return  # 非 UTF-8 文本由扩展名/体积检查覆盖
    for regex, desc in ABSOLUTE_PATH_PATTERNS:
        for m in regex.finditer(text):
            problems.append(f"{rel}:{line_of(text, m.start())} 绝对路径 —— {desc}: {m.group(0)[:80]}")
    for regex, desc in SECRET_PATTERNS:
        for m in regex.finditer(text):
            problems.append(f"{rel}:{line_of(text, m.start())} 疑似凭据 —— {desc}: {m.group(0)[:40]}")
    for regex, desc in FORBIDDEN_LABEL_PATTERNS:
        for m in regex.finditer(text):
            problems.append(f"{rel}:{line_of(text, m.start())} {desc}: {m.group(0)}")


def is_pinned_jbrowse_vendor_asset(rel: str) -> bool:
    """Return whether a file belongs to the pinned upstream JBrowse runtime.

    Minified upstream bundles legitimately contain terms such as ``password``
    (UI labels) and source-map build paths.  They are not project-authored
    content and are integrity-checked by ``validate_jbrowse_release.py``.
    BTED configs, catalogs and data assets remain subject to the strict scan.
    """

    return rel.startswith("jbrowse/static/")


def check_links(path: Path, site_root: Path, rel: str, problems: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    parser = LinkCollector()
    parser.feed(text)
    for lineno, attr, value in parser.links:
        target = value.strip()
        if target.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        target_path = target.split("#", 1)[0].split("?", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(site_root)
        except ValueError:
            problems.append(f"{rel}:{lineno} 内部链接越出站点目录: {target}")
            continue
        if not resolved.exists():
            # JBrowse is intentionally delivered as a versioned GitHub Release
            # asset and unpacked beside the site during Pages deployment.  The
            # source-only site may therefore contain valid future links before
            # the bundle is staged.  Once a ``jbrowse`` directory exists in the
            # validation root, missing files inside it are treated as errors.
            for staged_name in ("jbrowse", "downloads"):
                staged_root = site_root / staged_name
                try:
                    resolved.relative_to(staged_root)
                    if not staged_root.exists():
                        break
                except ValueError:
                    continue
            else:
                problems.append(f"{rel}:{lineno} 内部链接无法解析: {target}")
                continue
            if not staged_root.exists():
                continue
            problems.append(f"{rel}:{lineno} 内部链接无法解析: {target}")


def main() -> int:
    site_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not site_dir.is_dir():
        print(f"FAIL 站点目录不存在: {site_dir}")
        return 1

    problems: list[str] = []
    warnings: list[str] = []
    file_count = 0
    total_bytes = 0

    # 0. 必需文件
    for name in REQUIRED_FILES:
        if not (site_dir / name).is_file():
            problems.append(f"缺少必需文件: {name}")

    for root, _dirs, files in os.walk(site_dir):
        for fname in files:
            fpath = Path(root) / fname
            rel = str(fpath.relative_to(site_dir))
            file_count += 1
            size = fpath.stat().st_size
            total_bytes += size

            # 1. 文件类型与体积
            suffixes = [s.lower() for s in fpath.suffixes]
            in_jbrowse = rel == "jbrowse" or rel.startswith("jbrowse/")
            in_downloads = rel == "downloads" or rel.startswith("downloads/")
            compound_suffix = "".join(suffixes[-2:]) if len(suffixes) >= 2 else (suffixes[-1] if suffixes else "")
            jbrowse_allowed = in_jbrowse and (
                fpath.suffix.lower() in ALLOWED_JBROWSE_SUFFIXES
                or compound_suffix in ALLOWED_JBROWSE_SUFFIXES
            )
            download_allowed = in_downloads and fpath.suffix.lower() in ALLOWED_DOWNLOAD_SUFFIXES
            if any(s in FORBIDDEN_EXTENSIONS for s in suffixes) and not (jbrowse_allowed or download_allowed):
                problems.append(f"{rel} 禁止的文件类型（原始数据/工作簿/压缩包/坐标文件）")
            size_limit = MAX_JBROWSE_FILE_BYTES if in_jbrowse else (MAX_DOWNLOAD_FILE_BYTES if in_downloads else MAX_FILE_BYTES)
            if size > size_limit:
                problems.append(f"{rel} 文件过大（{size} 字节 > {size_limit} 字节上限）")

            # 2-4. 文本内容扫描
            if fpath.suffix.lower() in TEXT_EXTENSIONS and not is_pinned_jbrowse_vendor_asset(rel):
                scan_text(fpath, rel, problems)

            # 5. HTML 内部链接完整性
            if fpath.suffix.lower() in (".html", ".htm"):
                check_links(fpath, site_dir, rel, problems)

    print("=" * 60)
    print("BTED 站点产物验证")
    print(f"站点目录: {site_dir}")
    print(f"文件总数: {file_count}，总体积: {total_bytes} 字节")
    print("检查项: 必需文件 / 文件类型与体积 / 绝对路径 / 凭据 / 证据标签 / 内部链接")
    print("=" * 60)

    for w in warnings:
        print(f"WARN  {w}")
    if problems:
        for p in problems:
            print(f"FAIL  {p}")
        print(f"\n验证未通过：{len(problems)} 个问题。")
        return 1
    print("PASS  全部检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
