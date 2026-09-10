#!/usr/bin/env python3
"""Parse BATTER paper supplementary files and Zenodo data.

Outputs to repo/site/data/augmentation/:
  - gene_clusters.tsv       (MOESM2, sheet 1)
  - rfam_families.tsv       (MOESM2, sheet 2)
  - stem_loop_properties.tsv (MOESM3, sheet 1)
  - rho_dependency.tsv       (MOESM3, sheet 2)
  - combined-statistics.tsv  (Zenodo, copied)
"""

import csv
import os
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("openpyxl not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

OUT = Path("D:/SEU/实习/BATTER数据整理/BTED/repo/site/data/augmentation")
OUT.mkdir(parents=True, exist_ok=True)

MOESM2 = Path("D:/SEU/实习/BATTER数据整理/main/文献X-BATTER/40168_2026_2454_MOESM2_ESM.xlsx")
MOESM3 = Path("D:/SEU/实习/BATTER数据整理/main/文献X-BATTER/40168_2026_2454_MOESM3_ESM.xlsx")

def safe(val):
    """Convert cell value to string or empty."""
    if val is None:
        return ""
    return str(val)


# ── MOESM2 Sheet 1: Gene clusters for augmentation ───────────────────
print("\n=== MOESM2 Sheet 1: Gene clusters ===")
wb = openpyxl.load_workbook(MOESM2, read_only=True)
print(f"  Sheets: {wb.sheetnames}")

# First sheet: gene clusters
sheet1 = wb[wb.sheetnames[0]]
rows = list(sheet1.iter_rows(values_only=True))
print(f"  Total rows (incl header): {len(rows)}")
print(f"  Header: {rows[0]}")
print(f"  Sample (row 1): {rows[1]}")
print(f"  Sample (row 2): {rows[2]}")

# Write gene_clusters.tsv
with open(OUT / "gene_clusters.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["cluster_id", "gene_name", "pfam_id", "description"])
    for r in rows[1:]:
        if not any(r):
            continue
        w.writerow([safe(r[0]), safe(r[1]), safe(r[2]) if len(r) > 2 else "", safe(r[3]) if len(r) > 3 else ""])

# Count unique clusters
cluster_ids = set()
for r in rows[1:]:
    if r[0] is not None:
        cluster_ids.add(str(r[0]))
print(f"  Unique cluster IDs: {len(cluster_ids)}")

# ── MOESM2 Sheet 2: Rfam families for augmentation ───────────────────
print("\n=== MOESM2 Sheet 2: Rfam families ===")
sheet2 = wb[wb.sheetnames[1]]
rows2 = list(sheet2.iter_rows(values_only=True))
print(f"  Total rows (incl header): {len(rows2)}")
print(f"  Header: {rows2[0]}")
print(f"  Sample (row 1): {rows2[1]}")

with open(OUT / "rfam_families.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["rfam_id", "name", "description", "category"])
    for r in rows2[1:]:
        if not any(r):
            continue
        w.writerow([safe(r[0]), safe(r[1]), safe(r[2]) if len(r) > 2 else "", safe(r[3]) if len(r) > 3 else ""])

print(f"  Rfam families written: {len(rows2) - 1}")

wb.close()

# ── MOESM3 Sheet 1: Stem-loop properties ─────────────────────────────
print("\n=== MOESM3 Sheet 1: Stem-loop properties ===")
wb3 = openpyxl.load_workbook(MOESM3, read_only=True)
print(f"  Sheets: {wb3.sheetnames}")

sheet3_1 = wb3[wb3.sheetnames[0]]
rows3_1 = list(sheet3_1.iter_rows(values_only=True))
print(f"  Total rows (incl header): {len(rows3_1)}")
print(f"  Header: {rows3_1[0]}")
print(f"  Sample (row 1): {rows3_1[1]}")

with open(OUT / "stem_loop_properties.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow([safe(c) for c in rows3_1[0]])
    for r in rows3_1[1:]:
        if not any(r):
            continue
        w.writerow([safe(c) for c in r])

print(f"  Stem-loop rows: {len(rows3_1) - 1}")

# ── MOESM3 Sheet 2: Rho dependency ───────────────────────────────────
print("\n=== MOESM3 Sheet 2: Rho dependency ===")
sheet3_2 = wb3[wb3.sheetnames[1]]
rows3_2 = list(sheet3_2.iter_rows(values_only=True))
print(f"  Total rows (incl header): {len(rows3_2)}")
print(f"  Header: {rows3_2[0]}")
print(f"  Sample (row 1): {rows3_2[1]}")

with open(OUT / "rho_dependency.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow([safe(c) for c in rows3_2[0]])
    for r in rows3_2[1:]:
        if not any(r):
            continue
        w.writerow([safe(c) for c in r])

print(f"  Rho dependency rows: {len(rows3_2) - 1}")

wb3.close()

print(f"\n✅ All MOESM tables written to {OUT}")