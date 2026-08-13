#!/usr/bin/env python3
"""Build the minimal, versioned BTED v0.2.0 JBrowse release archive.

The archive contains the pinned JBrowse 2 static application, 21 source
configurations, and only assets referenced by those configurations.  Test data,
duplicate portal files, raw sequencing files, and BATTER_S1_002 are excluded.
Every copied asset is renamed with its source ID to prevent cross-source
collisions.  Lalanne 2018 literature-curated overlays are omitted because their
supplementary fields are external-link-only; the public browser retains the
GEO-derived signal and called-candidate tracks.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote


RELEASE_VERSION = "v0.2.0"
SOURCE_CONFIGS = {
    "BATTER_S1_001": "config.json",
    "BATTER_S1_003": "bsub.config.json",
    "BATTER_S1_004": "ccre.config.json",
    "BATTER_S1_005": "vnat.config.json",
    "BATTER_S1_006": "warrier2018_spne.config.json",
    "BATTER_S1_007": "lee2019_sliv.config.json",
    "BATTER_S1_008": "thomason2019_pao1.config.json",
    "BATTER_S1_009": "vera2020_zm4.config.json",
    "BATTER_S1_010": "lee2020_save.config.json",
    "BATTER_S1_011": "lee2020_sgri.config.json",
    "BATTER_S1_012": "lee2020_scoe.config.json",
    "BATTER_S1_013": "lee2020_sliv.config.json",
    "BATTER_S1_014": "lee2020_stsu.config.json",
    "BATTER_S1_015": "lee2020_scla.config.json",
    "BATTER_S1_016": "lee2020_satcc15439.config.json",
    "BATTER_S1_017": "hwang2021_scla.config.json",
    "BATTER_S1_018": "synecho2021_pcc7338.config.json",
    "BATTER_S1_019": "synecho2021_pcc6803.config.json",
    "BATTER_S1_020": "forquet2022_ddad.config.json",
    "BATTER_S1_021": "adams2023_b31.config.json",
    "BATTER_S1_022": "mtb2023_termseq.config.json",
}
LALANNE_SOURCES = {
    "BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005",
}
RUNTIME_FILES = ["index.html", "manifest.json", "favicon.ico", "robots.txt", "version.txt"]
ASSEMBLY_GROUPS = {
    "GCF_000739105.1": ["BATTER_S1_007", "BATTER_S1_013"],
    "GCF_005519465.1": ["BATTER_S1_015", "BATTER_S1_017"],
}
STRAND_COLORS = {
    "+": "#2563A6",
    "-": "#D2691E",
}
LALANNE_COMPACT_TRACKS = {
    "BATTER_S1_001": {
        "prefix": "ecoli",
        "forward_signal": "experimental_3prime_signal.forward",
        "reverse_signal": "experimental_3prime_signal.reverse",
        "forward_signal_path": "data/batter_ecoli_pilot/processed/experimental_3prime_signal.forward.bedGraph",
        "reverse_signal_path": "data/batter_ecoli_pilot/processed/experimental_3prime_signal.reverse.bedGraph",
        "forward_endpoint": "experimental_3prime_geneproximal_candidates.forward",
        "reverse_endpoint": "experimental_3prime_geneproximal_candidates.reverse",
        "forward_endpoint_path": "data/batter_ecoli_pilot/processed/experimental_3prime_geneproximal_candidates.forward.browser.bed",
        "reverse_endpoint_path": "data/batter_ecoli_pilot/processed/experimental_3prime_geneproximal_candidates.reverse.browser.bed",
    },
    "BATTER_S1_003": {
        "prefix": "bsub",
        "forward_signal": "bsub_3prime_signal_forward",
        "reverse_signal": "bsub_3prime_signal_reverse",
        "forward_signal_path": "data/batter_bsub_pilot/processed/experimental_3prime_signal.forward.bedGraph",
        "reverse_signal_path": "data/batter_bsub_pilot/processed/experimental_3prime_signal.reverse.bedGraph",
        "forward_endpoint": "bsub_geneproximal_forward",
        "reverse_endpoint": "bsub_geneproximal_reverse",
        "forward_endpoint_path": "data/batter_bsub_pilot/processed/experimental_3prime_geneproximal_candidates.forward.browser.bed",
        "reverse_endpoint_path": "data/batter_bsub_pilot/processed/experimental_3prime_geneproximal_candidates.reverse.browser.bed",
    },
    "BATTER_S1_004": {
        "prefix": "ccre",
        "forward_signal": "ccre_3prime_signal_forward",
        "reverse_signal": "ccre_3prime_signal_reverse",
        "forward_signal_path": "data/batter_ccre_pilot/processed/experimental_3prime_signal.forward.bedGraph",
        "reverse_signal_path": "data/batter_ccre_pilot/processed/experimental_3prime_signal.reverse.bedGraph",
        "forward_endpoint": "ccre_geneproximal_forward",
        "reverse_endpoint": "ccre_geneproximal_reverse",
        "forward_endpoint_path": "data/batter_ccre_pilot/processed/experimental_3prime_geneproximal_candidates.forward.browser.bed",
        "reverse_endpoint_path": "data/batter_ccre_pilot/processed/experimental_3prime_geneproximal_candidates.reverse.browser.bed",
    },
    "BATTER_S1_005": {
        "prefix": "vnat",
        "forward_signal": "vnat_3prime_signal_forward",
        "reverse_signal": "vnat_3prime_signal_reverse",
        "forward_signal_path": "data/batter_vnat_pilot/processed/experimental_3prime_signal.forward.bedGraph",
        "reverse_signal_path": "data/batter_vnat_pilot/processed/experimental_3prime_signal.reverse.bedGraph",
        "forward_endpoint": "vnat_geneproximal_forward",
        "reverse_endpoint": "vnat_geneproximal_reverse",
        "forward_endpoint_path": "data/batter_vnat_pilot/processed/experimental_3prime_geneproximal_candidates.forward.browser.bed",
        "reverse_endpoint_path": "data/batter_vnat_pilot/processed/experimental_3prime_geneproximal_candidates.reverse.browser.bed",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def walk_uris(value: Any) -> list[tuple[dict[str, Any], str]]:
    found: list[tuple[dict[str, Any], str]] = []
    if isinstance(value, dict):
        if isinstance(value.get("uri"), str):
            found.append((value, value["uri"]))
        for child in value.values():
            found.extend(walk_uris(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(walk_uris(child))
    return found


def is_restricted_lalanne_track(track: dict[str, Any]) -> bool:
    searchable = " ".join(
        [str(track.get("name", "")), str(track.get("trackId", ""))]
        + [str(item) for item in track.get("category", [])]
    ).lower()
    return "literature" in searchable or "curated_terminator" in searchable


def is_reference_annotation(track: dict[str, Any]) -> bool:
    searchable = " ".join(
        [str(track.get("name", "")), str(track.get("trackId", ""))]
        + [str(item) for item in track.get("category", [])]
    ).lower()
    return "reference annotation" in searchable or "gene annotation" in searchable


def track_by_id(tracks: list[dict[str, Any]], track_id: str) -> dict[str, Any]:
    matches = [track for track in tracks if track.get("trackId") == track_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one track {track_id!r}; found {len(matches)}")
    return matches[0]


def adapter_with_strand_style(
    track: dict[str, Any], strand: str, replacement_uri: str | None = None,
) -> dict[str, Any]:
    adapter = copy.deepcopy(track["adapter"])
    if replacement_uri is not None:
        locations = [container for container, uri in walk_uris(adapter) if uri.endswith(".bw")]
        if len(locations) != 1:
            raise ValueError(f"{track.get('trackId')}: expected one BigWig location")
        locations[0]["uri"] = replacement_uri
    adapter["name"] = "+ strand" if strand == "+" else "− strand"
    adapter["source"] = strand
    adapter["color"] = STRAND_COLORS[strand]
    return adapter


def compact_signal_bigwigs(
    source_id: str,
    prefix: str,
    settings: dict[str, str],
    input_root: Path,
    package_root: Path,
    fai_path: Path,
) -> tuple[Path, Path]:
    """Create signed-log display BigWigs; raw BigWigs remain untouched.

    The display-only files are deliberately uncompressed.  The pinned JBrowse
    2.17 bigwig reader fails on compressed UCSC blocks generated in the local
    arm64 toolchain, while the uncompressed v4 files pass both UCSC and browser
    checks.  This affects release size only, not signal values or core data.
    """

    converter_candidates = [
        shutil.which("bedGraphToBigWig"),
        "/opt/miniconda3/envs/batter-browser/bin/bedGraphToBigWig",
    ]
    converter = next((Path(item) for item in converter_candidates if item and Path(item).is_file()), None)
    if converter is None:
        raise FileNotFoundError(
            "bedGraphToBigWig is required to build the compact signed-log display assets"
        )

    with tempfile.TemporaryDirectory(prefix="bted-strand-display-") as temp_dir:
        temp_root = Path(temp_dir)
        chrom_sizes = temp_root / "chrom.sizes"
        chrom_sizes.write_text(
            "".join(
                f"{fields[0]}\t{fields[1]}\n"
                for line in fai_path.read_text(encoding="utf-8").splitlines()
                if line and len(fields := line.split("\t")) >= 2
            ),
            encoding="utf-8",
        )
        outputs: list[Path] = []
        for direction, sign in (("forward", 1.0), ("reverse", -1.0)):
            input_bedgraph = input_root / settings[f"{direction}_signal_path"]
            if not input_bedgraph.is_file():
                raise FileNotFoundError(f"{source_id}: missing canonical signal {input_bedgraph}")
            transformed = temp_root / f"{direction}.signed-log10.bedGraph"
            with input_bedgraph.open(encoding="utf-8") as source, transformed.open("w", encoding="utf-8") as destination:
                for line_number, line in enumerate(source, start=1):
                    if not line.strip():
                        continue
                    fields = line.rstrip("\n").split("\t")
                    if len(fields) != 4:
                        raise ValueError(f"{input_bedgraph}:{line_number}: expected bedGraph4")
                    value = float(fields[3])
                    if value < 0:
                        raise ValueError(f"{input_bedgraph}:{line_number}: raw signal is negative")
                    display_value = sign * math.log10(1.0 + value)
                    destination.write("\t".join([*fields[:3], f"{display_value:.8g}"]) + "\n")
            output = package_root / "assets" / (
                f"{source_id}__{prefix}_experimental_3prime_signal."
                f"{direction}.signed-log10-ui-v4.bw"
            )
            subprocess.run(
                [str(converter), "-unc", str(transformed), str(chrom_sizes), str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            outputs.append(output)
    return outputs[0], outputs[1]


def gff3_escape(value: object) -> str:
    """Percent-encode a GFF3 attribute value without obscuring stable IDs."""

    return quote(str(value), safe="._:-|")


def candidate_metadata(path: Path) -> dict[str, dict[str, str]]:
    """Load the canonical candidate table used to enrich browser-only features."""

    import csv

    if not path.is_file():
        raise FileNotFoundError(f"Missing canonical candidate table: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    metadata = {row["end_id"]: row for row in rows}
    if len(metadata) != len(rows):
        raise ValueError(f"{path}: duplicate end_id values")
    return metadata


def combined_endpoint_gff3(
    source_id: str,
    prefix: str,
    settings: dict[str, str],
    input_root: Path,
    package_root: Path,
) -> Path:
    """Build a rich, display-only GFF3 from the canonical strand-specific BEDs.

    The public BED6 contract remains unchanged.  This GFF3 is a browser asset so
    that a clicked mark exposes its stable ID, 1-based coordinate, strand, raw
    signal support and evidence boundary instead of an anonymous dot feature.
    """

    rows: list[tuple[str, int, int, str, str]] = []
    for direction, expected_strand in (("forward", "+"), ("reverse", "-")):
        browser_bed = input_root / settings[f"{direction}_endpoint_path"]
        endpoint_bed = Path(str(browser_bed).replace(".browser.bed", ".bed"))
        candidate_tsv = endpoint_bed.parent / f"experimental_3prime_candidates.{direction}.tsv"
        details = candidate_metadata(candidate_tsv)
        if not endpoint_bed.is_file():
            raise FileNotFoundError(f"{source_id}: missing canonical endpoint BED {endpoint_bed}")
        for line_number, line in enumerate(endpoint_bed.read_text(encoding="utf-8").splitlines(), start=1):
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) != 6:
                raise ValueError(f"{endpoint_bed}:{line_number}: expected BED6")
            ref_name, start_text, end_text, end_id, bed_score, strand = fields
            if strand != expected_strand:
                raise ValueError(
                    f"{endpoint_bed}:{line_number}: expected strand {expected_strand}, found {strand}"
                )
            if end_id not in details:
                raise ValueError(f"{endpoint_bed}:{line_number}: {end_id} absent from {candidate_tsv}")
            detail = details[end_id]
            start_0based, end_0based = int(start_text), int(end_text)
            position = end_0based
            if end_0based != start_0based + 1:
                raise ValueError(f"{endpoint_bed}:{line_number}: endpoint is not one base")
            if (
                detail["chrom"] != ref_name
                or int(detail["biological_coordinate_1based"]) != position
                or detail["strand"] != strand
            ):
                raise ValueError(f"{endpoint_bed}:{line_number}: BED/TSV identity mismatch")
            attributes = {
                "ID": end_id,
                "Name": f"{strand} strand candidate at {ref_name}:{position}",
                "source_id": source_id,
                "sample_id": detail["sample_id"],
                "biological_coordinate_1based": position,
                "strand_symbol": strand,
                "read_support_raw": detail["read_support"],
                "bed6_score_capped": bed_score,
                "assay": detail["assay"],
                "evidence_class": "called_endpoint",
                "evidence_interpretation": "local_signal_peak",
                "warning": "Signal-derived candidate peak; not an experimentally proven terminator.",
            }
            for key in ("upstream_gene", "upstream_locus_tag", "distance_to_gene_end_nt", "context"):
                if detail.get(key):
                    attributes[key] = detail[key]
            attribute_text = ";".join(
                f"{key}={gff3_escape(value)}" for key, value in attributes.items()
            )
            rows.append((
                ref_name,
                position,
                position,
                strand,
                "\t".join([
                    ref_name,
                    "BTED",
                    "called_endpoint",
                    str(position),
                    str(position),
                    detail["read_support"],
                    strand,
                    ".",
                    attribute_text,
                ]),
            ))

    rows.sort(key=lambda item: (item[0], item[1], item[3], item[4]))
    destination = package_root / "assets" / f"{source_id}__{prefix}_geneproximal.combined.browser.gff3"
    destination.write_text(
        "##gff-version 3\n" + "".join(f"{line}\n" for _ref, _start, _end, _strand, line in rows),
        encoding="utf-8",
    )
    return destination


def compact_lalanne_tracks(
    source_id: str,
    tracks: list[dict[str, Any]],
    input_root: Path,
    package_root: Path,
    fai_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build the compact public view while retaining separate full-evidence tracks."""

    settings = LALANNE_COMPACT_TRACKS[source_id]
    prefix = str(settings["prefix"])
    reference_tracks = [copy.deepcopy(track) for track in tracks if is_reference_annotation(track)]
    if len(reference_tracks) != 1:
        raise ValueError(f"{source_id}: expected one reference annotation track")
    assembly_names = copy.deepcopy(reference_tracks[0].get("assemblyNames", []))

    forward_signal = track_by_id(tracks, str(settings["forward_signal"]))
    reverse_signal = track_by_id(tracks, str(settings["reverse_signal"]))
    forward_endpoint = track_by_id(tracks, str(settings["forward_endpoint"]))
    reverse_endpoint = track_by_id(tracks, str(settings["reverse_endpoint"]))
    forward_display_bw, reverse_display_bw = compact_signal_bigwigs(
        source_id, prefix, settings, input_root, package_root, fai_path
    )

    signal_track = {
        "type": "MultiQuantitativeTrack",
        "trackId": f"{prefix}_strand_aware_3prime_signal",
        "name": "Signal · blue + above zero · orange − below zero",
        "description": (
            "Paired strand-specific Rend-seq signal from one experiment. "
            "Blue values above zero denote the + strand; orange values below zero denote "
            "the − strand. Display values are sign × log10(1 + raw signal). Negative values "
            "encode strand only, not negative experimental abundance. Raw untransformed "
            "strand tracks remain available in Full evidence view."
        ),
        "adapter": {
            "type": "MultiWiggleAdapter",
            "subadapters": [
                adapter_with_strand_style(
                    forward_signal, "+", f"assets/{forward_display_bw.name}"
                ),
                adapter_with_strand_style(
                    reverse_signal, "-", f"assets/{reverse_display_bw.name}"
                ),
            ],
        },
        "displays": [{
            "type": "MultiLinearWiggleDisplay",
            "displayId": f"{prefix}_strand_aware_3prime_signal-MultiLinearWiggleDisplay",
            "defaultRendering": "xyplot",
            "height": 170,
            "showSidebar": True,
        }],
        "category": ["BTED compact view", "Observed signal"],
        "assemblyNames": assembly_names,
        "metadata": {
            "evidence_class": "observed_signal",
            "strand_encoding": "+ strand blue; - strand orange",
            "display_transform": "sign(strand) * log10(1 + raw_signal)",
            "scale_note": "Paired series share one zero-centred display; raw tracks are retained separately.",
        },
    }

    combined_gff3 = combined_endpoint_gff3(
        source_id, prefix, settings, input_root, package_root
    )
    endpoint_track = {
        "type": "FeatureTrack",
        "trackId": f"{prefix}_geneproximal_combined",
        "name": "Candidates · blue → + strand · orange ← − strand",
        "description": (
            "Context-filtered candidate 3′-end peaks. The BED strand remains authoritative; "
            "right-pointing marks are + strand and left-pointing marks are − strand. "
            "Candidates are not terminator conclusions."
        ),
        "adapter": {
            "type": "Gff3Adapter",
            "gffLocation": {
                "uri": f"assets/{combined_gff3.name}",
                "locationType": "UriLocation",
            },
        },
        "displays": [{
            "type": "LinearBasicDisplay",
            "displayId": f"{prefix}_geneproximal_combined-LinearBasicDisplay",
            "height": 56,
            "renderer": {
                "type": "SvgFeatureRenderer",
                "showLabels": False,
                "showDescriptions": False,
                "color1": (
                    f"jexl:get(feature,'strand')==1?'{STRAND_COLORS['+']}':"
                    f"get(feature,'strand')==-1?'{STRAND_COLORS['-']}':'#6B7280'"
                ),
                "height": 12,
            },
        }],
        "category": ["BTED compact view", "Called endpoints"],
        "assemblyNames": assembly_names,
        "metadata": {
            "evidence_class": "called_endpoint",
            "strand_encoding": "+ strand blue/right arrow; - strand orange/left arrow",
            "score_interpretation": "GFF3 score is the raw 3-prime-end signal support at the called position; BED6 score remains capped at 1000.",
            "click_for_details": "Stable end ID, 1-based coordinate, strand, raw support, context and evidence warning.",
            "warning": "Signal-derived candidate peak; not an experimentally proven terminator.",
        },
    }

    evidence_tracks: list[dict[str, Any]] = []
    for original in (forward_signal, reverse_signal, forward_endpoint, reverse_endpoint):
        evidence = copy.deepcopy(original)
        evidence["category"] = ["Full evidence view", *(evidence.get("category") or [])]
        evidence_tracks.append(evidence)
    return [*reference_tracks, signal_track, endpoint_track, *evidence_tracks], [
        combined_gff3.name,
        forward_display_bw.name,
        reverse_display_bw.name,
    ]


def restore_canonical_lalanne_endpoint_assets(
    source_id: str,
    tracks: list[dict[str, Any]],
    input_root: Path,
    package_root: Path,
) -> None:
    """Replace legacy viewer copies with each source's canonical processed BEDs."""

    settings = LALANNE_COMPACT_TRACKS[source_id]
    for direction in ("forward", "reverse"):
        track = track_by_id(tracks, str(settings[f"{direction}_endpoint"]))
        packaged_uris = [uri for _container, uri in walk_uris(track["adapter"]) if uri.endswith(".bed")]
        if len(packaged_uris) != 1:
            raise ValueError(f"{source_id}/{direction}: expected one packaged endpoint BED")
        canonical = input_root / str(settings[f"{direction}_endpoint_path"])
        if not canonical.is_file():
            raise FileNotFoundError(f"{source_id}/{direction}: missing canonical endpoint BED {canonical}")
        shutil.copy2(canonical, package_root / packaged_uris[0])


def remove_unreferenced_source_assets(
    source_id: str,
    source_assets: list[str],
    seen_destination_names: set[str],
    package_root: Path,
) -> None:
    """Delete source-prefixed files that were copied before track compaction."""

    kept_names = {Path(asset).name for asset in source_assets}
    for path in (package_root / "assets").glob(f"{source_id}__*"):
        if path.name not in kept_names:
            path.unlink()
            seen_destination_names.discard(path.name)


def reference_files(config: dict[str, Any], package_root: Path) -> tuple[Path, Path]:
    assembly = config.get("assemblies", [None])[0]
    if not isinstance(assembly, dict):
        raise ValueError("JBrowse config must contain one assembly")
    configured = [package_root / uri for _container, uri in walk_uris(assembly.get("sequence", {}))]
    fasta = [path for path in configured if path.suffix == ".fna"]
    fai = [path for path in configured if path.suffix == ".fai"]
    if len(fasta) != 1 or len(fai) != 1:
        raise ValueError("JBrowse assembly must reference one FASTA and one FAI")
    return fasta[0], fai[0]


def mixed_strand_display_region(
    tracks: list[dict[str, Any]], package_root: Path
) -> tuple[str, int, int] | None:
    """Choose an early, compact locus where both endpoint strands are visible."""

    compact_endpoints = [
        track for track in tracks
        if track.get("metadata", {}).get("evidence_class") == "called_endpoint"
        and "BTED compact view" in track.get("category", [])
    ]
    if len(compact_endpoints) != 1:
        return None
    gff_uris = [uri for _container, uri in walk_uris(compact_endpoints[0]) if uri.endswith(".gff3")]
    if len(gff_uris) != 1:
        return None
    gff_path = package_root / gff_uris[0]
    features: list[tuple[str, int, str]] = []
    for line_number, line in enumerate(gff_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 9 or fields[6] not in {"+", "-"}:
            raise ValueError(f"{gff_path}:{line_number}: invalid compact endpoint GFF3")
        features.append((fields[0], int(fields[3]), fields[6]))
    features.sort()
    opposite_pairs = [
        (left, right)
        for left, right in zip(features, features[1:])
        if left[0] == right[0] and left[2] != right[2]
    ]
    if not opposite_pairs:
        raise ValueError(f"{gff_path}: no adjacent opposite-strand endpoints")
    close_pair = next(
        (pair for pair in opposite_pairs if pair[1][1] - pair[0][1] <= 500),
        min(opposite_pairs, key=lambda pair: pair[1][1] - pair[0][1]),
    )
    left, right = close_pair
    return left[0], max(0, left[1] - 1 - 1_500), right[1] + 1_500


def default_linear_session(
    accession: str,
    assembly_name: str,
    tracks: list[dict[str, Any]],
    package_root: Path,
    fai_path: Path,
) -> dict[str, Any]:
    """Create a deterministic initial view around an informative endpoint locus."""

    endpoint_tracks = [track for track in tracks if not is_reference_annotation(track)]
    contig_lengths = {
        fields[0]: int(fields[1])
        for line in fai_path.read_text(encoding="utf-8").splitlines()
        if line and len(fields := line.split("\t")) >= 2
    }
    mixed_region = mixed_strand_display_region(tracks, package_root)
    if mixed_region is not None:
        ref_name, view_start, view_end = mixed_region
    else:
        bed_paths = [
            package_root / uri
            for track in endpoint_tracks
            for _container, uri in walk_uris(track)
            if uri.endswith(".bed")
        ]
        first_bed = next((path for path in bed_paths if path.is_file() and path.stat().st_size), None)
        if first_bed is None:
            raise ValueError(f"{accession}: cannot choose a default region without an endpoint track")
        first_fields = next(line for line in first_bed.read_text(encoding="utf-8").splitlines() if line).split("\t")
        ref_name, feature_start, feature_end = first_fields[0], int(first_fields[1]), int(first_fields[2])
        view_start = max(0, feature_start - 5_000)
        view_end = feature_end + 5_000
    if ref_name not in contig_lengths:
        raise ValueError(f"{accession}: endpoint contig {ref_name} is absent from the shared FAI")
    view_end = min(contig_lengths[ref_name], view_end)

    session_tracks = []
    default_tracks = [
        track for track in tracks
        if is_reference_annotation(track) or "BTED compact view" in track.get("category", [])
    ]
    if len(default_tracks) == 1:
        default_tracks = tracks
    for index, track in enumerate(default_tracks, start=1):
        track_id = str(track["trackId"])
        track_type = str(track.get("type", "FeatureTrack"))
        if track_type == "MultiQuantitativeTrack":
            display_type = "MultiLinearWiggleDisplay"
        elif track_type == "QuantitativeTrack":
            display_type = "LinearWiggleDisplay"
        else:
            display_type = "LinearBasicDisplay"
        session_tracks.append({
            "id": f"bted_track_{index}",
            "type": track_type,
            "configuration": track_id,
            "minimized": False,
            "displays": [{
                "id": f"bted_display_{index}",
                "type": display_type,
                "configuration": f"{track_id}-{display_type}",
            }],
        })
    return {
        "name": f"BTED {accession} · independent source tracks",
        "views": [{
            "id": "bted_linear_genome_view",
            "type": "LinearGenomeView",
            "offsetPx": 0,
            "bpPerPx": max((view_end - view_start) / 1_000, 1),
            "displayedRegions": [{
                "refName": ref_name,
                "start": view_start,
                "end": view_end,
                "reversed": False,
                "assemblyName": assembly_name,
            }],
            "tracks": session_tracks,
        }],
    }


def copy_runtime(viewer_root: Path, package_root: Path) -> None:
    for name in RUNTIME_FILES:
        source = viewer_root / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing JBrowse runtime file: {source}")
        shutil.copy2(source, package_root / name)
    static_source = viewer_root / "static"
    if not static_source.is_dir():
        raise FileNotFoundError(f"Missing JBrowse runtime directory: {static_source}")
    shutil.copytree(static_source, package_root / "static")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True, help="Local BGIRNA working tree")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    input_root = args.input_root.expanduser().resolve()
    viewer_root = input_root / "browser/jbrowse2/viewer"
    output_dir = args.output_dir.expanduser().resolve()
    package_name = "BTED-v0.2.0-jbrowse"
    package_root = output_dir / package_name
    archive_path = output_dir / "BTED-v0.2.0-jbrowse-assets.tar.gz"

    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True)
    (package_root / "assets").mkdir()
    copy_runtime(viewer_root, package_root)

    catalog: dict[str, Any] = {
        "release_version": RELEASE_VERSION,
        "jbrowse_version": (viewer_root / "version.txt").read_text(encoding="utf-8").strip(),
        "source_count": len(SOURCE_CONFIGS),
        "excluded_sources": ["BATTER_S1_002"],
        "sources": {},
        "assemblies": {},
    }
    seen_destination_names: set[str] = set()

    for source_id, config_name in SOURCE_CONFIGS.items():
        config_path = viewer_root / config_name
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if source_id in LALANNE_SOURCES:
            config["tracks"] = [track for track in config.get("tracks", []) if not is_restricted_lalanne_track(track)]

        source_assets: list[str] = []
        for uri_container, uri in walk_uris(config):
            if "://" in uri or uri.startswith("data:"):
                raise ValueError(f"{source_id}: remote/data URI is not allowed in the portable package: {uri}")
            source_asset = (config_path.parent / uri).resolve()
            try:
                source_asset.relative_to(viewer_root.resolve())
            except ValueError as exc:
                raise ValueError(f"{source_id}: asset escapes viewer root: {uri}") from exc
            if not source_asset.is_file():
                raise FileNotFoundError(f"{source_id}: missing configured asset: {source_asset}")
            destination_name = f"{source_id}__{source_asset.name}"
            if destination_name not in seen_destination_names:
                shutil.copy2(source_asset, package_root / "assets" / destination_name)
                seen_destination_names.add(destination_name)
            uri_container["uri"] = f"assets/{destination_name}"
            source_assets.append(f"assets/{destination_name}")

        if source_id in LALANNE_COMPACT_TRACKS:
            restore_canonical_lalanne_endpoint_assets(
                source_id, config.get("tracks", []), input_root, package_root
            )
            compact_fai = reference_files(config, package_root)[1]
            config["tracks"], generated_assets = compact_lalanne_tracks(
                source_id, config.get("tracks", []), input_root, package_root, compact_fai
            )
            for asset_name in generated_assets:
                seen_destination_names.add(asset_name)
                source_assets.append(f"assets/{asset_name}")
            configured_after_compaction = set(uris for _container, uris in walk_uris(config))
            source_assets = [asset for asset in source_assets if asset in configured_after_compaction]
            remove_unreferenced_source_assets(
                source_id, source_assets, seen_destination_names, package_root
            )

        if not config.get("assemblies"):
            raise ValueError(f"{source_id}: config has no assembly")
        source_assembly_name = str(config["assemblies"][0]["name"])
        source_fai = reference_files(config, package_root)[1]
        config["defaultSession"] = default_linear_session(
            source_id,
            source_assembly_name,
            config.get("tracks", []),
            package_root,
            source_fai,
        )

        config_output = package_root / f"{source_id}.config.json"
        config_output.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        config_text = config_output.read_text(encoding="utf-8").lower()
        if source_id in LALANNE_SOURCES and ("literature_curated" in config_text or "curated terminator" in config_text):
            raise ValueError(f"{source_id}: restricted Lalanne literature overlay remains in public config")
        catalog["sources"][source_id] = {
            "config": config_output.name,
            "asset_count": len(set(source_assets)),
            "assets": sorted(set(source_assets)),
            "track_count": len(config.get("tracks", [])),
        }

    (package_root / "assemblies").mkdir()
    for assembly_accession, source_ids in ASSEMBLY_GROUPS.items():
        source_configs = [
            json.loads((package_root / f"{source_id}.config.json").read_text(encoding="utf-8"))
            for source_id in source_ids
        ]
        reference_pairs = [reference_files(config, package_root) for config in source_configs]
        fasta_hashes = {sha256(pair[0]) for pair in reference_pairs}
        fai_hashes = {sha256(pair[1]) for pair in reference_pairs}
        if len(fasta_hashes) != 1 or len(fai_hashes) != 1:
            raise ValueError(
                f"{assembly_accession}: sources cannot share one view because FASTA/FAI content differs"
            )

        combined = copy.deepcopy(source_configs[0])
        assembly_name = f"BTED_{assembly_accession.replace('.', '_')}"
        combined_assembly = combined["assemblies"][0]
        combined_assembly["name"] = assembly_name
        combined_assembly["displayName"] = f"BTED {assembly_accession} · {len(source_ids)} source tracks"
        combined_assembly["sequence"]["trackId"] = f"{assembly_name}_refseq"

        combined_tracks: list[dict[str, Any]] = []
        reference_tracks = [track for track in source_configs[0].get("tracks", []) if is_reference_annotation(track)]
        if len(reference_tracks) != 1:
            raise ValueError(f"{assembly_accession}: expected one reference annotation track")
        reference_track = copy.deepcopy(reference_tracks[0])
        reference_track["assemblyNames"] = [assembly_name]
        combined_tracks.append(reference_track)

        endpoint_track_ids: list[str] = []
        for source_id, config in zip(source_ids, source_configs):
            endpoint_tracks = [track for track in config.get("tracks", []) if not is_reference_annotation(track)]
            if not endpoint_tracks:
                raise ValueError(f"{source_id}: no source endpoint track found for assembly view")
            for track in endpoint_tracks:
                track = copy.deepcopy(track)
                track["assemblyNames"] = [assembly_name]
                track["name"] = f"{source_id} · {track.get('name', 'endpoint track')}"
                track["category"] = ["BTED source tracks", source_id]
                combined_tracks.append(track)
                endpoint_track_ids.append(str(track.get("trackId")))

        combined["tracks"] = combined_tracks
        combined["defaultSession"] = default_linear_session(
            assembly_accession,
            assembly_name,
            combined_tracks,
            package_root,
            reference_pairs[0][1],
        )
        # The combined config lives one directory below the source configs.
        # Keep all resources portable by resolving them through ../assets/.
        for uri_container, uri in walk_uris(combined):
            if uri.startswith("assets/"):
                uri_container["uri"] = f"../{uri}"
        combined_path = package_root / "assemblies" / f"{assembly_accession}.config.json"
        combined_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        catalog["assemblies"][assembly_accession] = {
            "config": str(combined_path.relative_to(package_root)),
            "source_ids": source_ids,
            "reference_source_id": source_ids[0],
            "endpoint_track_ids": endpoint_track_ids,
            "reference_fasta_sha256": next(iter(fasta_hashes)),
            "reference_fai_sha256": next(iter(fai_hashes)),
        }

    (package_root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package_files = sorted(path for path in package_root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    (package_root / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(path)}  {path.relative_to(package_root)}\n" for path in package_files),
        encoding="utf-8",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(package_root, arcname=package_name)
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{sha256(archive_path)}  {archive_path.name}\n", encoding="utf-8")

    total_bytes = sum(path.stat().st_size for path in package_root.rglob("*") if path.is_file())
    print(
        f"PASS  {archive_path.name}: {len(SOURCE_CONFIGS)} source configs, "
        f"{len(ASSEMBLY_GROUPS)} multi-track assembly configs, "
        f"{len(seen_destination_names)} referenced assets, {total_bytes / 1024 / 1024:.1f} MiB unpacked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
