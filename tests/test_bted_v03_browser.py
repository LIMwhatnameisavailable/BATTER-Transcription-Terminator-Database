"""Focused offline tests for the dynamic assembly JBrowse configuration."""

from __future__ import annotations

import unittest
from typing import Any, Mapping

from backend.app.browser import BrowserConfigUnavailable, build_jbrowse_config
from backend.app.contracts import ReleaseContext, RepositoryNotFound
from backend.app.service import ReadService


RELEASE = ReleaseContext("v0.3.0", "published", "a" * 64, 17)
ASSEMBLY = "GCF_000739105.1"


def asset(asset_id: str, kind: str, path: str) -> dict[str, Any]:
    return {"asset_id": asset_id, "asset_kind": kind, "logical_path": path, "sha256": "b" * 64}


def source(source_id: str, *, evidence: str = "author_called_endpoint", with_signal: bool = False, audit: bool = False) -> dict[str, Any]:
    source_assets = [asset(f"{source_id}--bed", "bed", f"records/{source_id}/endpoints.bed")]
    if with_signal:
        source_assets.append(asset(f"{source_id}--signal-plus", "bigwig", f"tracks/{source_id}.plus.bw"))
        source_assets.append(asset(f"{source_id}--signal-minus", "bigwig", f"tracks/{source_id}.minus.bw"))
    return {
        "source_id": source_id,
        "release_status": "audit_only" if audit else "published_standardized",
        "has_jbrowse": not audit,
        "record_count": 0 if audit else 10,
        "species": "Escherichia coli str. K-12",
        "assay_family": "Term-seq",
        "evidence_class": "NA" if audit else evidence,
        "publication": {
            "pmid": "12345678", "doi": "10.1000/test", "title": f"Paper {source_id}",
            "year": 2020, "journal": "Test journal",
            "links": {"pubmed": "https://pubmed.ncbi.nlm.nih.gov/12345678/", "doi": "https://doi.org/10.1000/test"},
        },
        "accessions": [{"namespace": "GEO", "accession": "GSE123", "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123"}],
        "assembly": {"accession": ASSEMBLY},
        "assets": [] if audit else source_assets,
    }


def assembly(*, include_fasta: bool = True, include_bigwig: bool = False) -> dict[str, Any]:
    reference_assets = [
        asset("assembly--gff", "gff3", "reference/genes.gff3.gz"),
        asset("assembly--tbi", "tbi", "reference/genes.gff3.gz.tbi"),
    ]
    if include_fasta:
        reference_assets.extend([asset("assembly--fasta", "fasta", "reference/reference.fna"), asset("assembly--fai", "fai", "reference/reference.fna.fai")])
    return {
        "assembly_accession": ASSEMBLY,
        "organism_name": "Escherichia coli",
        "strain": "K-12",
        "contigs": [{"accession": "CP000001.1", "name": "CP000001.1", "length_bp": 100000}],
        "assets": reference_assets,
        "source_tracks": [
            {"source_id": "BATTER_S1_007", "record_count": 10, "release_status": "published_standardized", "has_jbrowse": True},
            {"source_id": "BATTER_S1_002", "record_count": 0, "release_status": "audit_only", "has_jbrowse": False},
        ],
        "endpoint_count": 10,
    }


class BundleRepository:
    def __init__(self, *, with_signal: bool = False) -> None:
        self.assembly = assembly()
        self.sources = [source("BATTER_S1_007", with_signal=with_signal), source("BATTER_S1_002", audit=True)]

    def resolve_release(self, release_version: str | None = None) -> ReleaseContext:
        if release_version not in (None, RELEASE.release_version):
            raise RepositoryNotFound("release not found")
        return RELEASE

    def get_jbrowse_bundle(self, release: ReleaseContext, assembly_accession: str) -> Mapping[str, Any] | None:
        return {"assembly": self.assembly, "sources": self.sources} if assembly_accession == ASSEMBLY else None


class TestDynamicJBrowseConfig(unittest.TestCase):
    def test_shared_reference_and_independent_source_track_with_metadata(self) -> None:
        config = build_jbrowse_config(assembly(), [source("BATTER_S1_007"), source("BATTER_S1_002", audit=True)], RELEASE)
        self.assertEqual(len(config["assemblies"]), 1)
        self.assertEqual(config["assemblies"][0]["sequence"]["adapter"]["type"], "IndexedFastaAdapter")
        self.assertEqual(len(config["tracks"]), 2)  # GFF3 + one published endpoint BED
        endpoint_tracks = [track for track in config["tracks"] if track["category"][0] == "BTED source tracks"]
        self.assertEqual([track["metadata"]["source_id"] for track in endpoint_tracks], ["BATTER_S1_007"])
        metadata = endpoint_tracks[0]["metadata"]
        self.assertEqual(metadata["publication_url"], "https://pubmed.ncbi.nlm.nih.gov/12345678/")
        self.assertEqual(metadata["raw_data_urls"]["GSE123"], "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123")
        self.assertIn("/api/v1/assets/BATTER_S1_007--bed", endpoint_tracks[0]["adapter"]["bedLocation"]["uri"])
        self.assertNotIn("BATTER_S1_002", str(config))

    def test_bigwig_is_optional_and_retains_raw_signal_metadata(self) -> None:
        config = build_jbrowse_config(assembly(), [source("BATTER_S1_007", with_signal=True)], RELEASE)
        signals = [track for track in config["tracks"] if track["type"] == "MultiQuantitativeTrack"]
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["metadata"]["evidence_class"], "observed_signal")
        self.assertEqual(signals[0]["metadata"]["normalization"], "none")
        self.assertEqual(signals[0]["metadata"]["display_transform"], "none")
        self.assertIn("+ / − strands", signals[0]["name"])
        self.assertEqual(len(signals[0]["adapter"]["subadapters"]), 2)
        no_signal = build_jbrowse_config(assembly(), [source("BATTER_S1_007")], RELEASE)
        self.assertFalse(any(track["type"] == "QuantitativeTrack" for track in no_signal["tracks"]))

    def test_private_or_missing_endpoint_bed_is_not_a_browser_source(self) -> None:
        missing = source("BATTER_S1_007")
        missing["assets"] = [asset for asset in missing["assets"] if asset["asset_kind"] != "bed"]
        with self.assertRaises(BrowserConfigUnavailable):
            build_jbrowse_config(assembly(), [missing], RELEASE)

        private = source("BATTER_S1_007")
        private["assets"][0]["is_public"] = False
        with self.assertRaises(BrowserConfigUnavailable):
            build_jbrowse_config(assembly(), [private], RELEASE)

        with self.assertRaises(BrowserConfigUnavailable):
            build_jbrowse_config(
                assembly(),
                [source("BATTER_S1_008"), missing],
                RELEASE,
                default_source_id="BATTER_S1_007",
            )

    def test_service_builds_dynamic_config_and_rejects_audit_source_default(self) -> None:
        service = ReadService(BundleRepository())
        config = service.jbrowse_config(None, ASSEMBLY)
        self.assertEqual(config["metadata"]["assembly_accession"], ASSEMBLY)
        selected = service.jbrowse_config(None, ASSEMBLY, source_id="BATTER_S1_007")
        self.assertEqual(selected["metadata"]["source_ids"], ["BATTER_S1_007"])
        with self.assertRaises(Exception):
            service.jbrowse_config(None, ASSEMBLY, source_id="BATTER_S1_002")


if __name__ == "__main__":
    unittest.main()
