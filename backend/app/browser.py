"""Build a small, release-aware JBrowse 2 configuration for one assembly.

The builder only references public assets already returned by the read
repository.  It does not discover files, fetch objects, merge source tracks,
or infer missing signal.  In particular, source-level publication/accession
metadata is copied into track metadata so a browser view remains traceable.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote

from .contracts import ReleaseContext


class BrowserConfigUnavailable(RuntimeError):
    """The selected assembly has no sufficient registered public browser assets."""


def _asset_id(asset: Mapping[str, Any]) -> str | None:
    value = asset.get("asset_id", asset.get("asset_key"))
    return str(value) if value else None


def _assets(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping) and _asset_id(item)]


def _assembly_assets(assembly: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = _assets(assembly.get("assets"))
    # The prototype registry used a role->asset mapping.  Accepting it here
    # keeps the API adapter compatible without making it a second data source.
    reference_assets = assembly.get("reference_assets")
    if isinstance(reference_assets, Mapping):
        for role, value in reference_assets.items():
            if isinstance(value, Mapping):
                item = dict(value)
            else:
                item = {"asset_id": value}
            item.setdefault("role", role)
            if _asset_id(item) and not any(_asset_id(existing) == _asset_id(item) for existing in result):
                result.append(item)
    return result


def _kind(asset: Mapping[str, Any]) -> str:
    return str(asset.get("asset_kind", asset.get("role", ""))).lower()


def is_public_asset(asset: Mapping[str, Any]) -> bool:
    """Treat repository rows without the SQL-only flag as public."""

    value = asset.get("is_public")
    if isinstance(value, str):
        return value.lower() not in {"false", "0", "no"}
    return value is not False and value != 0


def _find(assets: Sequence[Mapping[str, Any]], kind: str) -> dict[str, Any] | None:
    matches = [
        dict(item)
        for item in assets
        if _kind(item) == kind and _asset_id(item) and is_public_asset(item)
    ]
    return sorted(matches, key=lambda item: str(_asset_id(item)))[0] if matches else None


def _uri(asset: Mapping[str, Any], asset_base: str) -> str:
    asset_id = _asset_id(asset)
    if not asset_id:
        raise BrowserConfigUnavailable("browser asset has no stable asset_id")
    return f"{asset_base.rstrip('/')}/{quote(asset_id, safe='')}"


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _publication(source: Mapping[str, Any]) -> dict[str, Any]:
    publication = source.get("publication")
    result = dict(publication) if isinstance(publication, Mapping) else {}
    for field in ("pmid", "doi", "pmc", "year", "journal", "title"):
        if field not in result and source.get(field) is not None:
            result[field] = source[field]
    links = result.get("links")
    return {"pmid": result.get("pmid"), "doi": result.get("doi"), "pmc": result.get("pmc"),
            "year": result.get("year"), "journal": result.get("journal"), "title": result.get("title"),
            "links": dict(links) if isinstance(links, Mapping) else {}}


def _raw_accessions(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = source.get("accessions", source.get("raw_accessions", []))
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return []
    return [dict(item) for item in raw if isinstance(item, Mapping)]


def _public_source(source: Mapping[str, Any]) -> bool:
    return (
        str(source.get("release_status", "")) == "published_standardized"
        and int(source.get("record_count", 0) or 0) > 0
        and has_public_endpoint_bed(source)
    )


def _source_metadata(source: Mapping[str, Any]) -> dict[str, Any]:
    publication = _publication(source)
    publication_links = publication.get("links", {}) if isinstance(publication.get("links"), Mapping) else {}
    publication_url = next(
        (publication_links.get(key) for key in ("pubmed", "doi", "pmc") if publication_links.get(key)),
        None,
    )
    raw_data_urls = {
        str(item.get("accession")): item.get("url")
        for item in _raw_accessions(source)
        if item.get("accession") and item.get("url")
    }
    return {
        "source_id": source.get("source_id"),
        "assay_family": source.get("assay_family"),
        "evidence_class": source.get("evidence_class"),
        "record_count": int(source.get("record_count", 0) or 0),
        "publication": publication,
        "publication_url": publication_url,
        "raw_accessions": _raw_accessions(source),
        "raw_data_urls": raw_data_urls,
        "redistribution_status": source.get("redistribution_status"),
        "provenance": {
            "release_version": source.get("provenance", {}).get("release_version")
            if isinstance(source.get("provenance"), Mapping) else None,
            "source_manifest_sha256": source.get("manifest_sha256")
            or (source.get("provenance", {}).get("source_manifest_sha256")
                if isinstance(source.get("provenance"), Mapping) else None),
        },
    }


def _strand_from_asset(asset: Mapping[str, Any]) -> str | None:
    for key in ("strand", "signal_strand", "track_strand"):
        value = str(asset.get(key, "")).strip()
        if value in {"+", "-"}:
            return value
    path = str(asset.get("logical_path", asset.get("asset_key", ""))).lower()
    if any(token in path for token in ("plus", "forward", ".fwd.", "_p.", "-p.")):
        return "+"
    if any(token in path for token in ("minus", "reverse", ".rev.", "_m.", "-m.")):
        return "-"
    return None


def _source_assets(source: Mapping[str, Any], fallback_track: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    assets = _assets(source.get("assets"))
    if not assets and fallback_track is not None:
        assets = _assets(fallback_track.get("assets"))
    return assets


def has_public_endpoint_bed(source: Mapping[str, Any], fallback_track: Mapping[str, Any] | None = None) -> bool:
    """Return whether a source has a registered public endpoint BED asset."""

    return _find(_source_assets(source, fallback_track), "bed") is not None


def _endpoint_track(source: Mapping[str, Any], assets: Sequence[Mapping[str, Any]], assembly_name: str, asset_base: str) -> dict[str, Any] | None:
    bed = _find(assets, "bed")
    if bed is None:
        return None
    source_id = str(source.get("source_id"))
    track_id = f"bted_{_safe_id(source_id).lower()}_endpoints"
    metadata = _source_metadata(source)
    metadata["signal_semantics"] = "source endpoint coordinates; not a per-site terminator-function claim"
    return {
        "type": "FeatureTrack",
        "trackId": track_id,
        "name": f"{source_id} · {source.get('evidence_class', 'endpoint').replace('_', ' ')}",
        "adapter": {"type": "BedAdapter", "bedLocation": {"uri": _uri(bed, asset_base), "locationType": "UriLocation"}},
        "displays": [{"type": "LinearBasicDisplay", "displayId": f"{track_id}_display", "showLabels": False, "height": 38}],
        "category": ["BTED source tracks", source_id, str(source.get("evidence_class", "endpoint"))],
        "assemblyNames": [assembly_name],
        "metadata": metadata,
    }


def _signal_tracks(source: Mapping[str, Any], assets: Sequence[Mapping[str, Any]], assembly_name: str, asset_base: str) -> list[dict[str, Any]]:
    # A registered BigWig is an observed-signal asset.  This does not change
    # the source's endpoint evidence class: a curated endpoint source may also
    # expose a separate raw signal layer.
    bigwigs = sorted(
        (asset for asset in assets if _kind(asset) == "bigwig" and is_public_asset(asset)),
        key=lambda item: str(_asset_id(item)),
    )
    if not bigwigs:
        return []
    source_id = str(source.get("source_id"))

    def single_track(bigwig: Mapping[str, Any], index: int) -> dict[str, Any]:
        strand = _strand_from_asset(bigwig)
        suffix = f" ({strand} strand)" if strand else " (strand not specified)"
        track_id = f"bted_{_safe_id(source_id).lower()}_signal_{index}"
        metadata = _source_metadata(source)
        metadata.update({
            "evidence_class": "observed_signal",
            "signal_semantics": "raw observed signal",
            "normalization": "none",
            "display_transform": "none",
            "strand": strand,
            "coverage_asset_sha256": bigwig.get("sha256"),
        })
        return {
            "type": "QuantitativeTrack",
            "trackId": track_id,
            "name": f"{source_id} · observed signal{suffix}",
            "adapter": {"type": "BigWigAdapter", "bigWigLocation": {"uri": _uri(bigwig, asset_base), "locationType": "UriLocation"}},
            "displays": [{"type": "LinearWiggleDisplay", "displayId": f"{track_id}_display"}],
            "category": ["Observed signal", source_id] + ([f"{strand} strand"] if strand else []),
            "assemblyNames": [assembly_name],
            "metadata": metadata,
        }

    strands = {_strand_from_asset(bigwig): bigwig for bigwig in bigwigs}
    if "+" in strands and "-" in strands:
        plus = strands["+"]
        minus = strands["-"]
        track_id = f"bted_{_safe_id(source_id).lower()}_signal_strands"
        metadata = _source_metadata(source)
        metadata.update({
            "evidence_class": "observed_signal",
            "signal_semantics": "raw observed signal",
            "normalization": "none",
            "display_transform": "none",
            "strand_encoding": "+ strand blue; - strand orange; both retain positive raw values",
            "coverage_asset_sha256": {"+": plus.get("sha256"), "-": minus.get("sha256")},
        })
        compact = {
            "type": "MultiQuantitativeTrack",
            "trackId": track_id,
            "name": f"{source_id} · observed signal (+ / − strands)",
            "adapter": {
                "type": "MultiWiggleAdapter",
                "subadapters": [
                    {"type": "BigWigAdapter", "bigWigLocation": {"uri": _uri(plus, asset_base), "locationType": "UriLocation"}, "name": "+ strand", "source": "+", "color": "#2563A6"},
                    {"type": "BigWigAdapter", "bigWigLocation": {"uri": _uri(minus, asset_base), "locationType": "UriLocation"}, "name": "− strand", "source": "-", "color": "#D2691E"},
                ],
            },
            "displays": [{"type": "MultiLinearWiggleDisplay", "displayId": f"{track_id}_display", "defaultRendering": "xyplot", "height": 150}],
            "category": ["Observed signal", source_id, "+ / − strands"],
            "assemblyNames": [assembly_name],
            "metadata": metadata,
        }
        leftovers = [item for item in bigwigs if item is not plus and item is not minus]
        return [compact, *[single_track(item, index + 1) for index, item in enumerate(leftovers)]]
    return [single_track(item, index + 1) for index, item in enumerate(bigwigs)]


def build_jbrowse_config(
    assembly: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
    release: ReleaseContext,
    *,
    asset_base: str = "/api/v1/assets",
    default_source_id: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic JBrowse config for one validated assembly."""

    assembly_accession = str(assembly.get("assembly_accession", ""))
    if not assembly_accession:
        raise BrowserConfigUnavailable("assembly accession is missing")
    assembly_assets = _assembly_assets(assembly)
    fasta = _find(assembly_assets, "fasta")
    fai = _find(assembly_assets, "fai")
    if fasta is None or fai is None:
        raise BrowserConfigUnavailable("assembly FASTA and FAI assets are not both public")

    source_by_id: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        source_id = str(source.get("source_id", ""))
        if source_id and _public_source(source):
            source_by_id[source_id] = source
    if default_source_id is not None and default_source_id not in source_by_id:
        raise BrowserConfigUnavailable("requested source is not a published browser track")
    if not source_by_id:
        raise BrowserConfigUnavailable("assembly has no published browser source")

    assembly_name = f"BTED_{_safe_id(assembly_accession).replace('.', '_')}"
    tracks: list[dict[str, Any]] = []
    gff3 = _find(assembly_assets, "gff3")
    tbi = _find(assembly_assets, "tbi")
    if gff3 is not None and tbi is not None:
        gene_track_id = f"{assembly_name}_genes"
        tracks.append({
            "type": "FeatureTrack",
            "trackId": gene_track_id,
            "name": "Reference gene annotation (GFF3)",
            "adapter": {
                "type": "Gff3TabixAdapter",
                "gffGzLocation": {"uri": _uri(gff3, asset_base), "locationType": "UriLocation"},
                "index": {"location": {"uri": _uri(tbi, asset_base), "locationType": "UriLocation"}, "indexType": "TBI"},
            },
            "category": ["Reference annotation"],
            "assemblyNames": [assembly_name],
            "metadata": {
                "feature_type": "gene features from registered GFF3",
                "strand_display": "standard GFF3 strand/arrow direction (+ right, - left)",
                "asset_sha256": {"gff3": gff3.get("sha256"), "tbi": tbi.get("sha256")},
                "provenance": {"release_version": release.release_version, "assembly_accession": assembly_accession},
            },
        })

    source_track_ids: list[str] = []
    for source_id in sorted(source_by_id):
        source = source_by_id[source_id]
        fallback = next((track for track in assembly.get("source_tracks", []) if isinstance(track, Mapping) and track.get("source_id") == source_id), None)
        source_assets = _source_assets(source, fallback)
        signal_tracks = _signal_tracks(source, source_assets, assembly_name, asset_base)
        tracks.extend(signal_tracks)
        source_track_ids.extend(track["trackId"] for track in signal_tracks)
        endpoint_track = _endpoint_track(source, source_assets, assembly_name, asset_base)
        if endpoint_track is not None:
            tracks.append(endpoint_track)
            source_track_ids.append(endpoint_track["trackId"])

    if not source_track_ids:
        raise BrowserConfigUnavailable("assembly has no public endpoint track asset")
    if default_source_id is not None:
        preferred = [track["trackId"] for track in tracks if track.get("metadata", {}).get("source_id") == default_source_id]
        remainder = [track_id for track_id in source_track_ids if track_id not in preferred]
        source_track_ids = preferred + remainder
    default_track_ids = [track["trackId"] for track in tracks if track["trackId"] == f"{assembly_name}_genes"] + source_track_ids
    contigs = [item for item in assembly.get("contigs", []) if isinstance(item, Mapping)]
    first_contig = sorted(contigs, key=lambda item: str(item.get("accession", "")))[0] if contigs else {}
    contig_name = str(first_contig.get("accession", first_contig.get("name", "")))
    length = int(first_contig.get("length_bp", 0) or 0)
    region = {"refName": contig_name, "start": 0, "end": min(length, 10000) if length else 10000, "reversed": False, "assemblyName": assembly_name}
    return {
        "assemblies": [{
            "name": assembly_name,
            "displayName": f"{assembly.get('organism_name') or assembly_accession} ({assembly_accession})",
            "sequence": {
                "type": "ReferenceSequenceTrack",
                "trackId": f"{assembly_name}_refseq",
                "adapter": {
                    "type": "IndexedFastaAdapter",
                    "fastaLocation": {"uri": _uri(fasta, asset_base), "locationType": "UriLocation"},
                    "faiLocation": {"uri": _uri(fai, asset_base), "locationType": "UriLocation"},
                },
            },
        }],
        "configuration": {},
        "connections": [],
        "tracks": tracks,
        "metadata": {
            "release": release.as_dict(),
            "assembly_accession": assembly_accession,
            "organism_name": assembly.get("organism_name"),
            "strain": assembly.get("strain"),
            "source_ids": sorted(source_by_id),
            "evidence_boundary": "published source tracks only; audit-only and prediction-only data excluded",
        },
        "defaultSession": {
            "name": f"{assembly_accession} · independent BTED source tracks",
            "views": [{
                "id": "bted_linear_genome_view",
                "type": "LinearGenomeView",
                "displayedRegions": [region],
                "tracks": [{
                    "id": f"bted_session_track_{index + 1}",
                    "type": "FeatureTrack" if track_id in {track["trackId"] for track in tracks if track["type"] == "FeatureTrack"} else "QuantitativeTrack",
                    "configuration": track_id,
                    "minimized": False,
                } for index, track_id in enumerate(default_track_ids)],
            }],
        },
    }
