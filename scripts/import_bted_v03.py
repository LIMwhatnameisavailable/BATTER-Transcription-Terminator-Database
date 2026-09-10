#!/usr/bin/env python3
"""Validate, materialize, and optionally write a BTED release.

``validate``, ``materialize`` and ``verify-bundle`` are read-only with respect
to the release and database.  The ``load-postgres`` and ``promote-postgres``
commands are separate, explicit operations: they require a confirmation flag
and a database URL environment variable, and never alter canonical release
files.

Examples::

    python3 scripts/import_bted_v03.py validate \
        --release-root data/public/v0.2.0
    python3 scripts/import_bted_v03.py validate \
        --release-root data/public/v0.2.0 --plan-json /tmp/bted-plan.json
    python3 scripts/import_bted_v03.py materialize \
        --release-root data/public/v0.2.0 \
        --output-dir /tmp/bted-v03-staging \
        --asset-origin-base https://example.test/assets \
        --generated-at-utc 2026-08-21T00:00:00Z
    python3 scripts/import_bted_v03.py verify-bundle \
        --bundle-dir /tmp/bted-v03-staging
    python3 scripts/import_bted_v03.py load-postgres \
        --bundle-dir /tmp/bted-v03-staging --confirm-write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.importer.canonical import validate_release  # noqa: E402
from backend.importer.materialize import MaterializationError, materialize_release  # noqa: E402
from backend.importer.postgres import (  # noqa: E402
    PostgresWriterError,
    connect_psycopg_from_env,
    load_bundle,
    promote_bundle,
    verify_bundle,
    verify_summary,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="校验 canonical release；不写数据库")
    validate.add_argument(
        "--release-root",
        default="data/public/v0.2.0",
        help="release root containing release_manifest.json (default: data/public/v0.2.0)",
    )
    validate.add_argument(
        "--repo-root",
        default=None,
        help="repository root; defaults to the conventional parent of --release-root",
    )
    validate.add_argument(
        "--plan-json",
        default=None,
        help="write the deterministic import plan to this path",
    )
    validate.add_argument(
        "--contig-registry",
        default=None,
        help=(
            "reference contig provenance TSV; defaults to "
            "data/registry/reference_contigs.v0.2.0.tsv under --repo-root"
        ),
    )
    materialize = subparsers.add_parser(
        "materialize",
        help="在不连接数据库的情况下生成确定性的 JSONL 写库前 staging bundle",
    )
    materialize.add_argument(
        "--release-root",
        default="data/public/v0.2.0",
        help="release root containing release_manifest.json (default: data/public/v0.2.0)",
    )
    materialize.add_argument(
        "--repo-root",
        default=None,
        help="repository root; defaults to the conventional parent of --release-root",
    )
    materialize.add_argument(
        "--contig-registry",
        default=None,
        help="reference contig provenance TSV; defaults to the tracked registry",
    )
    materialize.add_argument(
        "--output-dir",
        required=True,
        help="new or empty directory for the materialization bundle; non-empty directories are refused",
    )
    materialize.add_argument(
        "--asset-origin-base",
        required=True,
        help="HTTPS-only planned origin prefix; no remote request is made",
    )
    materialize.add_argument(
        "--generated-at-utc",
        default=None,
        help="fixed ISO-8601 timestamp for reproducible output (default: current UTC time)",
    )
    materialize.add_argument(
        "--jbrowse-asset-inventory",
        default=None,
        help=(
            "tracked browser asset TSV to merge into assets.jsonl; omitted by default "
            "to preserve the canonical 127-asset bundle"
        ),
    )
    materialize.add_argument(
        "--jbrowse-bundle-root",
        default=None,
        help=(
            "local JBrowse bundle root containing the registered reference GFF3/FAI files; "
            "gene import is enabled only together with --jbrowse-asset-inventory"
        ),
    )
    verify = subparsers.add_parser(
        "verify-bundle",
        help="只读验证 B1 JSONL bundle，不连接数据库",
    )
    verify.add_argument(
        "--bundle-dir",
        required=True,
        help="B1 materialization bundle directory",
    )
    for command, confirm_flag, help_text in (
        ("load-postgres", "--confirm-write", "将已验证 bundle 写入 PostgreSQL 单事务"),
        ("promote-postgres", "--confirm-promote", "在资产远程验证后发布一个已提交 release"),
    ):
        writer = subparsers.add_parser(command, help=help_text)
        writer.add_argument("--bundle-dir", required=True, help="B1 materialization bundle directory")
        writer.add_argument(confirm_flag, action="store_true", help="显式确认不可逆的数据库操作")
        writer.add_argument(
            "--database-url-env",
            default="BTED_DATABASE_URL",
            help="数据库 URL 所在环境变量名（默认 BTED_DATABASE_URL）",
        )
        writer.add_argument("--batch-size", type=int, default=1000, help="批量 endpoint/annotation 行数")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        report = validate_release(
            args.release_root,
            repo_root=args.repo_root,
            contig_registry=args.contig_registry,
        )
        if args.plan_json:
            plan_path = Path(args.plan_json).expanduser()
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                json.dumps(report.plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        json.dump(report.as_dict(), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if report.ok else 1
    if args.command == "materialize":
        try:
            result = materialize_release(
                args.release_root,
                repo_root=args.repo_root,
                contig_registry=args.contig_registry,
                output_dir=args.output_dir,
                asset_origin_base=args.asset_origin_base,
                generated_at_utc=args.generated_at_utc,
                jbrowse_asset_inventory=args.jbrowse_asset_inventory,
                jbrowse_bundle_root=args.jbrowse_bundle_root,
            )
        except MaterializationError as exc:
            json.dump({"ok": False, "error": str(exc)}, sys.stderr, ensure_ascii=False)
            sys.stderr.write("\n")
            return 1
        json.dump(
            {"ok": True, "output_dir": str(result.output_dir), "manifest": result.manifest},
            sys.stdout,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0
    if args.command == "verify-bundle":
        try:
            verification = verify_bundle(args.bundle_dir)
            json.dump(verify_summary(verification), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0
        except PostgresWriterError as exc:
            json.dump({"ok": False, "error": str(exc)}, sys.stderr, ensure_ascii=False)
            sys.stderr.write("\n")
            return 1
    if args.command in {"load-postgres", "promote-postgres"}:
        confirm_name = "confirm_write" if args.command == "load-postgres" else "confirm_promote"
        if not getattr(args, confirm_name):
            json.dump(
                {"ok": False, "error": f"{args.command} requires --{confirm_name.replace('_', '-') }"},
                sys.stderr,
                ensure_ascii=False,
            )
            sys.stderr.write("\n")
            return 2
        try:
            # Verify before importing psycopg or reading the database URL.  A
            # malformed bundle therefore cannot even begin an external DB
            # operation.
            verification = verify_bundle(args.bundle_dir)
            if args.command == "promote-postgres" and verification.manifest["asset_origin"]["asset_origin_status"] != "verified":
                raise PostgresWriterError(
                    "promotion requires asset_origin_status=verified after remote asset/Range audit"
                )
            connection = connect_psycopg_from_env(args.database_url_env)
            try:
                if args.command == "load-postgres":
                    result = load_bundle(args.bundle_dir, connection, batch_size=args.batch_size)
                    payload = {
                        "ok": True,
                        "release_version": result.release_version,
                        "run_id": result.run_id,
                        "status": result.status,
                        "counts": result.counts,
                    }
                else:
                    payload = {"ok": True, **promote_bundle(args.bundle_dir, connection)}
            finally:
                close = getattr(connection, "close", None)
                if callable(close):
                    close()
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
            sys.stdout.write("\n")
            return 0
        except PostgresWriterError as exc:
            json.dump({"ok": False, "error": str(exc)}, sys.stderr, ensure_ascii=False)
            sys.stderr.write("\n")
            return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
