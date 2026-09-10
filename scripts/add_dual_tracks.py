#!/usr/bin/env python3
"""Modify Lalanne JBrowse configs in-place to add dual signal tracks.

Existing single signal track (uses signed-log10 BigWigs) is preserved as
the "log" optional track (default_off: true). A new "linear (raw)" track
is added (default_off: false), referencing the untransformed .bw files.
"""

import json
import copy
from pathlib import Path

PREVIEW = Path("D:/SEU/实习/BATTER数据整理/BTED/_preview_site/jbrowse")
LALANNE_SOURCES = ["BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005"]

# Mapping of source_id → prefix used in BigWig asset names
BW_PREFIXES = {
    "BATTER_S1_001": "experimental_3prime_signal",      # no species prefix
    "BATTER_S1_003": "bsub_experimental_3prime_signal",  # has bsub_ prefix
    "BATTER_S1_004": "ccre_experimental_3prime_signal",
    "BATTER_S1_005": "vnat_experimental_3prime_signal",
}


def rewrite_config(source_id):
    config_path = PREVIEW / f"{source_id}.config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    tracks = config.get("tracks", [])
    signal_track_index = None
    signal_track = None
    for i, t in enumerate(tracks):
        if t.get("type") == "MultiQuantitativeTrack" and t.get("trackId", "").endswith("strand_aware_3prime_signal"):
            signal_track_index = i
            signal_track = t
            break

    if signal_track is None:
        print(f"  WARN: no signal track found, skipping")
        return

    prefix = signal_track["trackId"]
    bw_prefix = BW_PREFIXES[source_id]
    assembly_names = copy.deepcopy(signal_track.get("assemblyNames", []))

    # --- Track A: Log (existing track, modified) ---
    log_track = copy.deepcopy(signal_track)
    log_track["trackId"] = f"{prefix}_log"
    log_track["name"] = "Signal · log display"
    log_track["description"] = (
        "Paired strand-specific signal, displayed as sign × log10(1 + raw value) "
        "to compress dynamic range. Blue values above zero denote the + strand; "
        "orange values below zero denote the − strand. Raw untransformed strand tracks "
        "remain available in Full evidence view."
    )
    # Update displayId
    for disp in log_track.get("displays", []):
        old_id = disp.get("displayId", "")
        if old_id.endswith(f"{prefix}-MultiLinearWiggleDisplay"):
            disp["displayId"] = f"{prefix}_log-MultiLinearWiggleDisplay"

    # Ensure metadata exists
    if "metadata" not in log_track:
        log_track["metadata"] = {}
    log_track["metadata"]["display_transform"] = "sign(strand) * log10(1 + raw_signal)"
    log_track["metadata"]["default_off"] = True

    # --- Track B: Linear (raw) — cloned from log, but URIs point to raw .bw ---
    raw_track = copy.deepcopy(log_track)
    raw_track["trackId"] = f"{prefix}_raw"
    raw_track["name"] = "Signal · linear (raw)"
    raw_track["description"] = (
        "Paired strand-specific signal from one experiment, displayed as raw values (1:1). "
        "Blue values above zero denote the + strand; orange values below zero denote "
        "the − strand. Negative values encode strand only, not negative experimental abundance."
    )
    # Update displayId
    for disp in raw_track.get("displays", []):
        old_id = disp.get("displayId", "")
        if old_id.endswith(f"{prefix}_log-MultiLinearWiggleDisplay"):
            disp["displayId"] = f"{prefix}_raw-MultiLinearWiggleDisplay"

    # Point subadapter URIs to raw .bw (strip signed-log10-ui-v4 suffix)
    for sa in raw_track["adapter"]["subadapters"]:
        uri = sa["bigWigLocation"]["uri"]
        new_uri = uri.replace(".signed-log10-ui-v4.bw", ".bw")
        sa["bigWigLocation"]["uri"] = new_uri

    raw_track["metadata"]["display_transform"] = "raw (1:1)"
    raw_track["metadata"]["default_off"] = False

    # --- Replace the original signal track with both ---
    tracks[signal_track_index] = log_track
    tracks.insert(signal_track_index + 1, raw_track)

    # --- Update default session ---
    # Remove old signal track configuration reference, add both
    default_session = config.get("defaultSession")
    if default_session:
        for view in default_session.get("views", []):
            view_tracks = view.get("tracks", [])
            new_view_tracks = []
            for vt in view_tracks:
                vt_conf = vt.get("configuration", "")
                if vt_conf == prefix:
                    # Replace with log track (off by default in session too,
                    # but the metadata.default_off handles that in the UI)
                    new_view_tracks.append({
                        "id": vt["id"] + "_log",
                        "type": vt["type"],
                        "configuration": f"{prefix}_log",
                        "minimized": vt.get("minimized", False),
                        "displays": [
                            {
                                "id": vt["displays"][0]["id"] + "_log" if vt.get("displays") else f"{prefix}_log_display",
                                "type": vt["displays"][0]["type"] if vt.get("displays") else "MultiLinearWiggleDisplay",
                                "configuration": f"{prefix}_log-MultiLinearWiggleDisplay"
                            }
                        ]
                    })
                    # Add linear track (on by default in session)
                    new_view_tracks.append({
                        "id": vt["id"] + "_raw",
                        "type": vt["type"],
                        "configuration": f"{prefix}_raw",
                        "minimized": vt.get("minimized", False),
                        "displays": [
                            {
                                "id": vt["displays"][0]["id"] + "_raw" if vt.get("displays") else f"{prefix}_raw_display",
                                "type": vt["displays"][0]["type"] if vt.get("displays") else "MultiLinearWiggleDisplay",
                                "configuration": f"{prefix}_raw-MultiLinearWiggleDisplay"
                            }
                        ]
                    })
                else:
                    new_view_tracks.append(vt)
            view["tracks"] = new_view_tracks

    config["tracks"] = tracks
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  OK — log track: {log_track['trackId']}, raw track: {raw_track['trackId']}")


def main():
    for sid in LALANNE_SOURCES:
        print(f"\n{sid}:")
        rewrite_config(sid)


if __name__ == "__main__":
    main()